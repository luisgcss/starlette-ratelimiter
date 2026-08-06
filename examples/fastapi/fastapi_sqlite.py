"""FastAPI + SQLite rate limiter example.

Run from the repo root (editable install or path setup)::

    uv sync --group dev
    uv run --with "uvicorn[standard]" python examples/fastapi/fastapi_sqlite.py

Then::

    curl -i http://127.0.0.1:8000/ping
    # After 5 requests in a minute, expect HTTP 429
"""

from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI

from asgi_ratelimiter import Duration, Rate, configure_logging
from asgi_ratelimiter.fastapi import RateLimiter

configure_logging(level="INFO")

DB_PATH = Path(__file__).with_name("rate_limits.db")

limiter = RateLimiter(
	rate=Rate(limit=5, interval=Duration.MINUTE),
	identifier=lambda request: (
		request.client.host if request.client is not None else "default"
	),
	db_path=DB_PATH,
)

route_limiter = RateLimiter(
	rate=Rate(limit=2, interval=Duration.MINUTE),
	identifier=lambda request: "route:limited",
	db_path=DB_PATH,
)

app = FastAPI(
	title="asgi-ratelimiter FastAPI example",
	dependencies=[Depends(limiter)],
)


@app.get("/ping")
async def ping() -> dict[str, str]:
	return {"status": "ok"}


@app.get("/limited", dependencies=[Depends(route_limiter)])
async def limited() -> dict[str, str]:
	"""Stricter per-route limit (2/min), independent key from the app-wide limiter."""
	return {"status": "limited-ok"}


if __name__ == "__main__":
	import uvicorn

	uvicorn.run(app, host="127.0.0.1", port=8000)
