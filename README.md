# asgi-ratelimiter

Modular rate limiting for [ASGI](https://asgi.readthedocs.io/) apps — use
`Depends` with [FastAPI](https://fastapi.tiangolo.com/) or middleware with
[Starlette](https://www.starlette.io/).

Fixed-window limits backed by SQLite (stdlib). Redis extra is reserved for later.

## Requirements

- Python **3.14+**

## Install

```bash
# FastAPI (SQLite backend is built-in)
uv add "asgi-ratelimiter[fastapi]"

# Starlette
uv add "asgi-ratelimiter[starlette]"
```

Extras:

| Extra | Purpose |
|-------|---------|
| `fastapi` | FastAPI `Depends` integration |
| `starlette` | Starlette middleware |
| `sqlite` | Marker only (stdlib `sqlite3`; no extra packages) |
| `redis` | Declared for future Redis backend |

Combine extras: `uv add "asgi-ratelimiter[fastapi,sqlite]"`.

## Concepts

```python
from asgi_ratelimiter import Duration, Rate

# Allow 10 calls every 5 minutes
rate = Rate(limit=10, interval=Duration.MINUTE * 5)
```

`Duration` units: `SECOND`, `MINUTE`, `HOUR`, `DAY`, `WEEK` (multiply for longer windows).

## FastAPI

App-wide or per-route via `Depends(RateLimiter(...))`:

```python
from fastapi import Depends, FastAPI
from asgi_ratelimiter import Duration, Rate, configure_logging
from asgi_ratelimiter.fastapi import RateLimiter

configure_logging(level="INFO")

limiter = RateLimiter(
    rate=Rate(limit=5, interval=Duration.MINUTE),
    identifier=lambda request: request.client.host if request.client else "default",
    db_path="rate_limits.db",
)

app = FastAPI(dependencies=[Depends(limiter)])


@app.get("/ping")
async def ping() -> dict[str, str]:
    return {"status": "ok"}
```

Over limit → HTTP **429** with optional `Retry-After`.

Runnable example: [`examples/fastapi/fastapi_sqlite.py`](examples/fastapi/fastapi_sqlite.py)

## Starlette

```python
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import PlainTextResponse
from asgi_ratelimiter import Duration, Rate, configure_logging
from asgi_ratelimiter.starlette import RateLimitMiddleware

configure_logging(level="INFO")


async def homepage(request):
    return PlainTextResponse("ok")


app = Starlette(routes=[Route("/", homepage)])
app.add_middleware(
    RateLimitMiddleware,
    rate=Rate(limit=5, interval=Duration.MINUTE),
    db_path="rate_limits.db",
)
```

Runnable example: [`examples/starlette/starlette_sqlite.py`](examples/starlette/starlette_sqlite.py)

## Logging

```python
from asgi_ratelimiter import configure_logging, set_level

configure_logging(level="DEBUG")  # enable library logs (loguru)
set_level("WARNING")  # change level later
```

Logging is off until `configure_logging` (or `set_level`) is called.

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
uv run ruff format .
```

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[AGPL-3.0-or-later](LICENSE)

## Links

- Repository: https://github.com/luisgcss/asgi-ratelimiter
- Issues: https://github.com/luisgcss/asgi-ratelimiter/issues
- Changelog: [CHANGELOG.md](CHANGELOG.md)
