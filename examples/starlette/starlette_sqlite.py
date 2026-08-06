"""Starlette + SQLite rate limiter example.

Run from the repo root::

    uv sync --group dev
    uv run --with "uvicorn[standard]" python examples/starlette/starlette_sqlite.py

Then::

    curl -i http://127.0.0.1:8001/
    # After 5 requests in a minute, expect HTTP 429
"""

from __future__ import annotations

from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route

from asgi_ratelimiter import Duration, Rate, configure_logging
from asgi_ratelimiter.starlette import RateLimitMiddleware

configure_logging(level="INFO")

DB_PATH = Path(__file__).with_name("rate_limits.db")


async def homepage(_request: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


async def health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


app = Starlette(
    routes=[
        Route("/", homepage),
        Route("/health", health),
    ],
)
app.add_middleware(
    RateLimitMiddleware,
    rate=Rate(limit=5, interval=Duration.MINUTE),
    identifier=lambda request: (
        request.client.host if request.client is not None else "default"
    ),
    db_path=DB_PATH,
    key_prefix="example-starlette",
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
