"""Integration tests for Starlette RateLimitMiddleware on a full app."""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx2 import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from asgi_ratelimiter import Duration, Rate
from asgi_ratelimiter.backends.sqlite import SQLiteBackend
from asgi_ratelimiter.starlette import RateLimitMiddleware


async def homepage(_request: Request) -> PlainTextResponse:
	return PlainTextResponse("hello")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_starlette_app_rate_limit_flow(tmp_path: Path) -> None:
	db_path = tmp_path / "integration.db"
	backend = SQLiteBackend(db_path)
	app = Starlette(routes=[Route("/", homepage)])
	app.add_middleware(
		RateLimitMiddleware,
		rate=Rate(limit=1, interval=Duration.SECOND * 30),
		backend=backend,
		key_prefix="test-rl",
	)
	try:
		async with AsyncClient(
			transport=ASGITransport(app=app),
			base_url="http://testserver",
		) as client:
			ok = await client.get("/")
			blocked = await client.get("/")
		assert ok.status_code == 200
		assert ok.text == "hello"
		assert blocked.status_code == 429
		assert "Retry-After" in blocked.headers
	finally:
		await backend.close()
