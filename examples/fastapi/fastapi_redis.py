"""FastAPI + Redis rate limiter example.

Requires a Redis server (default ``redis://localhost:6379/0``).

Run from the repo root::

    uv sync --group dev
    uv run --with "uvicorn[standard]" python examples/fastapi/fastapi_redis.py

Then::

    curl -i http://127.0.0.1:8002/ping
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from redis.asyncio import Redis

from asgi_ratelimiter import Duration, Rate, configure_logging
from asgi_ratelimiter.backends.redis import RedisBackend
from asgi_ratelimiter.fastapi import RateLimiter

configure_logging(level="INFO")

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis = Redis.from_url(REDIS_URL)
backend = RedisBackend(redis=redis)

limiter = RateLimiter(
	rate=Rate(limit=5, interval=Duration.MINUTE),
	identifier=lambda request: (
		request.client.host if request.client is not None else "default"
	),
	backend=backend,
	key_prefix="example-fastapi-redis",
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
	yield
	await redis.aclose()


app = FastAPI(
	title="asgi-ratelimiter FastAPI Redis example",
	dependencies=[Depends(limiter)],
	lifespan=lifespan,
)


@app.get("/ping")
async def ping() -> dict[str, str]:
	return {"status": "ok"}


if __name__ == "__main__":
	import uvicorn

	uvicorn.run(app, host="127.0.0.1", port=8002)
