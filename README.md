# starlette-ratelimiter

Fast, async rate limiting for [Starlette](https://www.starlette.io/) apps.

> **Status:** core limiter API in progress. Starlette middleware not shipped yet.

## Install

```bash
# with uv
uv add starlette-ratelimiter

# with pip
pip install starlette-ratelimiter
```

## Usage

```python
from redis import Redis
from starlette_ratelimiter import Duration, Rate, RateLimiter

redis = Redis.from_url("redis://localhost:6379/0")

limiter = RateLimiter(
    rate=Rate(limit=1, interval=Duration.MINUTE * 5),
    identifier=lambda: "user:42",
    redis=redis,
)

if limiter.hit():
    ...  # allowed
else:
    ...  # rate limited
```

Omit `redis` to instantiate `Redis` from `redis_url` (default `redis://localhost:6379/0`). Pass `redis_class=RedisCluster` for cluster.

Omit `identifier` to use the default key identity (`"default"`).

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format .
```

## License

[AGPL-3.0-or-later](LICENSE)

## Links

- Repository: https://github.com/luisgcss/starlette-ratelimiter
- Issues: https://github.com/luisgcss/starlette-ratelimiter/issues
