# Contributing

Thanks for contributing to **asgi-ratelimiter**.

## Setup

Requires Python **3.14+** and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/luisgcss/asgi-ratelimiter.git
cd asgi-ratelimiter
uv sync --group dev
```

## Checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

### Pre-commit

Runs **ruff check** (with `--fix`), **ruff format**, and **pytest** on every commit:

```bash
uv sync --group dev
uv run pre-commit install
```

Run against all files once:

```bash
uv run pre-commit run --all-files
```

Format before opening a PR:

```bash
uv run ruff format .
uv run ruff check --fix .
```

## Branch workflow

1. Fork and branch from `develop` (or `master` for hotfixes).
2. Keep changes focused; match existing style (`src/` layout, type hints).
3. Add/update tests for behavior changes — suite targets high coverage.
4. Bump the package version (**semver**) in both `pyproject.toml` and
   `src/asgi_ratelimiter/__init__.py` (keep them identical), and update
   `tests/unit/test_version.py` + `CHANGELOG.md`:
   - **MAJOR** (`x.0.0`) — breaking public API changes
   - **MINOR** (`0.x.0`) — new features, backwards-compatible
   - **PATCH** (`0.0.x`) — bug fixes, docs-only, internal cleanups
5. Open a PR against `develop` with a short summary of *why*.

CI runs on `master` and `develop` (lint, test, build). Merges to `master` publish to PyPI when the version is new.

## Project layout

| Path | Role |
|------|------|
| `src/asgi_ratelimiter/` | Library code |
| `src/asgi_ratelimiter/fastapi/` | FastAPI `Depends` integration |
| `src/asgi_ratelimiter/starlette/` | Starlette middleware |
| `src/asgi_ratelimiter/backends/` | Storage backends (SQLite today) |
| `tests/` | Unit + integration tests |
| `examples/` | Runnable single-file demos |

## Examples

```bash
# FastAPI
uv run --with "asgi-ratelimiter[fastapi]" --with "uvicorn[standard]" \
  python examples/fastapi/fastapi_sqlite.py

# Starlette
uv run --with "asgi-ratelimiter[starlette]" --with "uvicorn[standard]" \
  python examples/starlette/starlette_sqlite.py
```

From a checked-out tree with `uv sync --group dev`, `uvicorn` may already be available via FastAPI; otherwise add it with `--with` as above.

## API notes

- Public imports live in `asgi_ratelimiter`, `asgi_ratelimiter.fastapi`, and `asgi_ratelimiter.starlette`.
- Prefer keyword args for new parameters.
- Do not break public APIs in minor/patch releases without a deprecation path.

## Reporting issues

Include Python version, OS, install extras (`[fastapi]`, etc.), minimal repro, and traceback.

## License

By contributing, you agree your work is licensed under the same
[AGPL-3.0-or-later](LICENSE) terms as this project.
