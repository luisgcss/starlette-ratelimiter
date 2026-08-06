# asgi-ratelimiter

Modular ASGI rate limiting for [FastAPI](https://fastapi.tiangolo.com/) and [Starlette](https://www.starlette.io/).

## Install

```bash
# FastAPI + SQLite
uv add "asgi-ratelimiter[fastapi,sqlite]"

# Starlette + SQLite
uv add "asgi-ratelimiter[starlette,sqlite]"
```

Optional extras: `fastapi`, `starlette`, `sqlite`, `redis` (Redis backend not implemented yet).

## FastAPI

```python
from fastapi import Depends, FastAPI
from asgi_ratelimiter import Duration, Rate, configure_logging
from asgi_ratelimiter.fastapi import RateLimiter

configure_logging(level="DEBUG")

app = FastAPI(
    dependencies=[
        Depends(
            RateLimiter(
                rate=Rate(limit=1, interval=Duration.MINUTE * 5),
                identifier=lambda request: request.client.host or "default",
            )
        )
    ]
)
```

## Starlette

```python
from starlette.applications import Starlette
from asgi_ratelimiter import Duration, Rate, configure_logging
from asgi_ratelimiter.starlette import RateLimitMiddleware

configure_logging(level="INFO")

app = Starlette()
app.add_middleware(
    RateLimitMiddleware,
    rate=Rate(limit=10, interval=Duration.MINUTE),
)
```

## Logging

```python
from asgi_ratelimiter import configure_logging, set_level

configure_logging(level="DEBUG")
set_level("WARNING")
```

## License

[AGPL-3.0-or-later](LICENSE)

## Links

- Repository: https://github.com/luisgcss/asgi-ratelimiter
- Issues: https://github.com/luisgcss/asgi-ratelimiter/issues
