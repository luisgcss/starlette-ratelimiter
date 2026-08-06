# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Nothing yet.

## [0.2.0] - 2026-08-06

### Changed

- Renamed package to `asgi-ratelimiter` with framework submodules
  (`asgi_ratelimiter.fastapi`, `asgi_ratelimiter.starlette`).
- Core no longer depends on Redis; storage is pluggable via backends.

### Added

- Optional extras: `fastapi`, `starlette`, `sqlite`, `redis` (Redis deferred).
- SQLite fixed-window backend (stdlib ``sqlite3``).
- Loguru-based `configure_logging` / `set_level`.
- FastAPI `Depends(RateLimiter(...))` integration.
- Starlette `RateLimitMiddleware`.

## [0.1.1] - 2026-08-06

### Added

- Initial modular core under previous `starlette-ratelimiter` name.

[Unreleased]: https://github.com/luisgcss/asgi-ratelimiter/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/luisgcss/asgi-ratelimiter/releases/tag/v0.2.0
[0.1.1]: https://github.com/luisgcss/asgi-ratelimiter/releases/tag/v0.1.1
