# Examples

Single-file demos for **asgi-ratelimiter**.

| File | Stack |
|------|--------|
| [`fastapi/fastapi_sqlite.py`](fastapi/fastapi_sqlite.py) | FastAPI `Depends` + SQLite |
| [`starlette/starlette_sqlite.py`](starlette/starlette_sqlite.py) | Starlette middleware + SQLite |

```bash
uv sync --group dev

# FastAPI — http://127.0.0.1:8000/ping
uv run --with "uvicorn[standard]" python examples/fastapi/fastapi_sqlite.py

# Starlette — http://127.0.0.1:8001/
uv run --with "uvicorn[standard]" python examples/starlette/starlette_sqlite.py
```

Each script writes a local `rate_limits.db` next to the example file.
