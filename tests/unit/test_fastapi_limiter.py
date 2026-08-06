"""Unit tests for FastAPI RateLimiter."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from asgi_ratelimiter import Duration, Rate
from asgi_ratelimiter.backends.base import HitResult
from asgi_ratelimiter.backends.sqlite import SQLiteBackend
from asgi_ratelimiter.fastapi import RateLimiter
from asgi_ratelimiter.fastapi import limiter as limiter_mod
from asgi_ratelimiter.fastapi.limiter import _default_identifier


@pytest.mark.unit
class TestRateLimiterValidation:
    def test_rejects_non_rate(self) -> None:
        with pytest.raises(TypeError, match="rate must be Rate"):
            RateLimiter(rate="not-a-rate")  # type: ignore[arg-type]

    def test_rejects_non_callable_identifier(self) -> None:
        with pytest.raises(TypeError, match="identifier must be callable"):
            RateLimiter(
                rate=Rate(limit=1, interval=Duration.SECOND),
                identifier="bad",  # type: ignore[arg-type]
            )

    def test_import_error_mentions_fastapi_extra(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(limiter_mod, "_HTTPException", None)
        monkeypatch.setattr(limiter_mod, "_Request", None)
        with pytest.raises(ImportError, match=r"asgi-ratelimiter\[fastapi\]"):
            RateLimiter(
                rate=Rate(limit=1, interval=Duration.SECOND),
                backend=AsyncMock(),
            )

    def test_default_backend_uses_sqlite(self, tmp_path: Path) -> None:
        limiter = RateLimiter(
            rate=Rate(limit=1, interval=Duration.SECOND),
            db_path=tmp_path / "default.db",
        )
        assert isinstance(limiter.backend, SQLiteBackend)

    def test_default_identifier_uses_client_host(self) -> None:
        request = MagicMock()
        request.client.host = "203.0.113.10"
        assert _default_identifier(request) == "203.0.113.10"

    def test_default_identifier_fallback_when_no_client(self) -> None:
        request = MagicMock()
        request.client = None
        assert _default_identifier(request) == "default"

    def test_default_identifier_fallback_when_empty_host(self) -> None:
        request = MagicMock()
        request.client.host = ""
        assert _default_identifier(request) == "default"


@pytest.mark.unit
@pytest.mark.asyncio
class TestRateLimiterCall:
    async def test_allows_under_limit(self) -> None:
        backend = AsyncMock()
        backend.hit.return_value = HitResult(allowed=True, count=1)
        limiter = RateLimiter(
            rate=Rate(limit=2, interval=Duration.MINUTE),
            backend=backend,
        )
        request = MagicMock()
        request.client.host = "127.0.0.1"

        await limiter(request)

        backend.hit.assert_awaited_once_with(
            "asgi-ratelimiter:127.0.0.1",
            limit=2,
            interval_seconds=60,
        )

    async def test_raises_429_over_limit(self) -> None:
        backend = AsyncMock()
        backend.hit.return_value = HitResult(
            allowed=False,
            count=2,
            retry_after=42,
        )
        limiter = RateLimiter(
            rate=Rate(limit=1, interval=Duration.SECOND),
            backend=backend,
            key_prefix="test",
        )
        request = MagicMock()
        request.client.host = "10.0.0.1"

        with pytest.raises(HTTPException) as exc_info:
            await limiter(request)

        assert exc_info.value.status_code == 429
        assert exc_info.value.detail == "Rate limit exceeded"
        assert exc_info.value.headers == {"Retry-After": "42"}
        backend.hit.assert_awaited_once_with(
            "test:10.0.0.1",
            limit=1,
            interval_seconds=1,
        )

    async def test_custom_identifier(self) -> None:
        backend = AsyncMock()
        backend.hit.return_value = HitResult(allowed=True, count=1)
        limiter = RateLimiter(
            rate=Rate(limit=5, interval=Duration.HOUR),
            backend=backend,
            identifier=lambda req: req.headers["x-api-key"],
        )
        request = MagicMock()
        request.headers = {"x-api-key": "user-42"}

        await limiter(request)

        backend.hit.assert_awaited_once_with(
            "asgi-ratelimiter:user-42",
            limit=5,
            interval_seconds=3600,
        )

    async def test_429_without_retry_after_omits_header(self) -> None:
        backend = AsyncMock()
        backend.hit.return_value = HitResult(
            allowed=False,
            count=3,
            retry_after=None,
        )
        limiter = RateLimiter(
            rate=Rate(limit=1, interval=Duration.SECOND),
            backend=backend,
        )
        request = MagicMock()
        request.client.host = "127.0.0.1"

        with pytest.raises(HTTPException) as exc_info:
            await limiter(request)

        assert exc_info.value.status_code == 429
        assert exc_info.value.headers is None
