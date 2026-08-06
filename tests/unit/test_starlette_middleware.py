"""Unit tests for Starlette RateLimitMiddleware."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx2 import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from asgi_ratelimiter import Duration, Rate
from asgi_ratelimiter.backends.base import HitResult
from asgi_ratelimiter.backends.sqlite import SQLiteBackend
from asgi_ratelimiter.starlette import RateLimitMiddleware
from asgi_ratelimiter.starlette.middleware import _default_identifier


async def _ok(_request: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


def _make_app(
    *,
    rate: Rate,
    backend: SQLiteBackend | None = None,
    identifier=None,
    db_path: str | Path | None = None,
) -> Starlette:
    app = Starlette(routes=[Route("/", _ok)])
    kwargs: dict = {
        "rate": rate,
        "identifier": identifier,
    }
    if backend is not None:
        kwargs["backend"] = backend
    if db_path is not None:
        kwargs["db_path"] = db_path
    app.add_middleware(RateLimitMiddleware, **kwargs)
    return app


@pytest.mark.unit
class TestRateLimitMiddlewareValidation:
    def test_rejects_non_rate(self) -> None:
        app = Starlette()
        with pytest.raises(TypeError, match="rate must be Rate"):
            RateLimitMiddleware(app, rate="bad")  # type: ignore[arg-type]

    def test_rejects_non_callable_identifier(self) -> None:
        app = Starlette()
        with pytest.raises(TypeError, match="identifier must be callable"):
            RateLimitMiddleware(
                app,
                rate=Rate(limit=1, interval=Duration.SECOND),
                identifier="bad",  # type: ignore[arg-type]
            )

    def test_rejects_empty_key_prefix(self) -> None:
        app = Starlette()
        with pytest.raises(ValueError, match="key_prefix"):
            RateLimitMiddleware(
                app,
                rate=Rate(limit=1, interval=Duration.SECOND),
                key_prefix="",
            )

    def test_default_backend_is_sqlite(self, tmp_path: Path) -> None:
        app = Starlette()
        mw = RateLimitMiddleware(
            app,
            rate=Rate(limit=1, interval=Duration.SECOND),
            db_path=tmp_path / "mw.db",
        )
        assert isinstance(mw.backend, SQLiteBackend)

    def test_default_identifier_without_client(self) -> None:
        request = MagicMock()
        request.client = None
        assert _default_identifier(request) == "default"

    def test_default_identifier_without_host(self) -> None:
        request = MagicMock()
        request.client = MagicMock()
        request.client.host = ""
        assert _default_identifier(request) == "default"


@pytest.mark.unit
@pytest.mark.asyncio
class TestRateLimitMiddleware:
    async def test_allows_under_limit(self, tmp_path: Path) -> None:
        backend = SQLiteBackend(tmp_path / "rate.db")
        app = _make_app(
            rate=Rate(limit=2, interval=Duration.MINUTE),
            backend=backend,
        )
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                first = await client.get("/")
                second = await client.get("/")
            assert first.status_code == 200
            assert first.text == "ok"
            assert second.status_code == 200
        finally:
            await backend.close()

    async def test_blocks_over_limit(self, tmp_path: Path) -> None:
        backend = SQLiteBackend(tmp_path / "rate.db")
        app = _make_app(
            rate=Rate(limit=1, interval=Duration.MINUTE),
            backend=backend,
        )
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                allowed = await client.get("/")
                denied = await client.get("/")
            assert allowed.status_code == 200
            assert denied.status_code == 429
            assert denied.json() == {"detail": "Rate limit exceeded"}
            assert "Retry-After" in denied.headers
            assert int(denied.headers["Retry-After"]) >= 0
        finally:
            await backend.close()

    async def test_denied_without_retry_after_header(self) -> None:
        backend = AsyncMock()
        backend.hit.return_value = HitResult(
            allowed=False,
            count=2,
            retry_after=None,
        )
        app = _make_app(
            rate=Rate(limit=1, interval=Duration.SECOND),
            backend=backend,
        )
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            denied = await client.get("/")
        assert denied.status_code == 429
        assert "retry-after" not in {k.lower() for k in denied.headers}

    async def test_custom_identifier(self, tmp_path: Path) -> None:
        backend = SQLiteBackend(tmp_path / "rate.db")
        app = _make_app(
            rate=Rate(limit=1, interval=Duration.MINUTE),
            backend=backend,
            identifier=lambda request: request.headers["x-user"],
        )
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                a1 = await client.get("/", headers={"x-user": "alice"})
                b1 = await client.get("/", headers={"x-user": "bob"})
                a2 = await client.get("/", headers={"x-user": "alice"})
            assert a1.status_code == 200
            assert b1.status_code == 200
            assert a2.status_code == 429
        finally:
            await backend.close()
