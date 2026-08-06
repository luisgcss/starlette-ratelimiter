"""Integration tests for FastAPI Depends(RateLimiter)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from httpx2 import ASGITransport, AsyncClient

from asgi_ratelimiter import Duration, Rate
from asgi_ratelimiter.backends.sqlite import SQLiteBackend
from asgi_ratelimiter.fastapi import RateLimiter


def _make_app(
    *,
    rate: Rate,
    backend: SQLiteBackend,
    identifier=None,
    app_level: bool = True,
) -> FastAPI:
    limiter = RateLimiter(rate=rate, backend=backend, identifier=identifier)
    if app_level:
        app = FastAPI(dependencies=[Depends(limiter)])

        @app.get("/ping")
        async def ping() -> dict[str, str]:
            return {"status": "ok"}

        return app

    app = FastAPI()

    @app.get("/ping", dependencies=[Depends(limiter)])
    async def ping() -> dict[str, str]:
        return {"status": "ok"}

    return app


@pytest.mark.integration
class TestFastAPIDependsSync:
    def test_under_limit_returns_200(self, tmp_path: Path) -> None:
        backend = SQLiteBackend(tmp_path / "rl.db")
        app = _make_app(
            rate=Rate(limit=2, interval=Duration.MINUTE),
            backend=backend,
        )
        with TestClient(app) as client:
            assert client.get("/ping").status_code == 200
            assert client.get("/ping").status_code == 200

    def test_over_limit_returns_429(self, tmp_path: Path) -> None:
        backend = SQLiteBackend(tmp_path / "rl.db")
        app = _make_app(
            rate=Rate(limit=1, interval=Duration.MINUTE),
            backend=backend,
        )
        with TestClient(app) as client:
            assert client.get("/ping").status_code == 200
            denied = client.get("/ping")
            assert denied.status_code == 429
            assert denied.json()["detail"] == "Rate limit exceeded"
            assert "retry-after" in denied.headers

    def test_custom_identifier_isolates_clients(self, tmp_path: Path) -> None:
        backend = SQLiteBackend(tmp_path / "rl.db")
        app = _make_app(
            rate=Rate(limit=1, interval=Duration.MINUTE),
            backend=backend,
            identifier=lambda request: request.headers.get("x-user", "anon"),
        )
        with TestClient(app) as client:
            assert client.get("/ping", headers={"x-user": "a"}).status_code == 200
            assert client.get("/ping", headers={"x-user": "b"}).status_code == 200
            assert client.get("/ping", headers={"x-user": "a"}).status_code == 429

    def test_route_level_depends(self, tmp_path: Path) -> None:
        backend = SQLiteBackend(tmp_path / "rl.db")
        app = _make_app(
            rate=Rate(limit=1, interval=Duration.MINUTE),
            backend=backend,
            app_level=False,
        )
        with TestClient(app) as client:
            assert client.get("/ping").status_code == 200
            assert client.get("/ping").status_code == 429


@pytest.mark.integration
@pytest.mark.asyncio
class TestFastAPIDependsAsync:
    async def test_httpx_asgi_transport(self, tmp_path: Path) -> None:
        backend = SQLiteBackend(tmp_path / "rl.db")
        app = _make_app(
            rate=Rate(limit=1, interval=Duration.MINUTE),
            backend=backend,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            assert (await client.get("/ping")).status_code == 200
            denied = await client.get("/ping")
            assert denied.status_code == 429
            assert denied.json()["detail"] == "Rate limit exceeded"
