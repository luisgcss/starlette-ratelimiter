"""Starlette + Redis rate limiter example.

Requires a Redis server (default ``redis://localhost:6379/0``).

Run from the repo root::

    uv sync --group dev
    uv run --with "uvicorn[standard]" python examples/starlette/starlette_redis.py

Then::

    curl -i http://127.0.0.1:8003/
"""

from __future__ import annotations

import os

from redis.asyncio import Redis
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from asgi_ratelimiter import Duration, Rate, configure_logging
from asgi_ratelimiter.backends.redis import RedisBackend
from asgi_ratelimiter.starlette import RateLimitMiddleware

configure_logging(level="INFO")

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis = Redis.from_url(REDIS_URL)
backend = RedisBackend(redis=redis)


async def homepage(_request: Request) -> PlainTextResponse:
	return PlainTextResponse("ok")


async def on_shutdown() -> None:
	await redis.aclose()


app = Starlette(
	routes=[Route("/", homepage)],
	on_shutdown=[on_shutdown],
)
app.add_middleware(
	RateLimitMiddleware,
	rate=Rate(limit=5, interval=Duration.MINUTE),
	identifier=lambda request: (
		request.client.host if request.client is not None else "default"
	),
	backend=backend,
	key_prefix="example-starlette-redis",
)


if __name__ == "__main__":
	import uvicorn

	uvicorn.run(app, host="127.0.0.1", port=8003)
