# Examples

Single-file demos for **asgi-ratelimiter**.

| File | Stack |
|------|--------|
| [`fastapi/fastapi_sqlite.py`](fastapi/fastapi_sqlite.py) | FastAPI `Depends` + SQLite |
| [`fastapi/fastapi_redis.py`](fastapi/fastapi_redis.py) | FastAPI `Depends` + Redis |
| [`starlette/starlette_sqlite.py`](starlette/starlette_sqlite.py) | Starlette middleware + SQLite |
| [`starlette/starlette_redis.py`](starlette/starlette_redis.py) | Starlette middleware + Redis |

```bash
uv sync --group dev

# FastAPI SQLite — http://127.0.0.1:8000/ping
uv run --with "uvicorn[standard]" python examples/fastapi/fastapi_sqlite.py

# FastAPI Redis — http://127.0.0.1:8002/ping (needs Redis)
REDIS_URL=redis://localhost:6379/0 \
  uv run --with "uvicorn[standard]" python examples/fastapi/fastapi_redis.py

# Starlette SQLite — http://127.0.0.1:8001/
uv run --with "uvicorn[standard]" python examples/starlette/starlette_sqlite.py

# Starlette Redis — http://127.0.0.1:8003/ (needs Redis)
REDIS_URL=redis://localhost:6379/0 \
  uv run --with "uvicorn[standard]" python examples/starlette/starlette_redis.py
```

SQLite examples write a local `rate_limits.db` next to the example file.
