# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Modular core API: `Duration`, `Rate`, `RateLimiter` with Redis / RedisCluster.
- Fixed-window limiting via Redis `INCR` + `EXPIRE`.
- Optional identifier callback (default: `"default"`).

### Changed

- Renamed project from `fast-ratelimiter` to `starlette-ratelimiter`.

## [0.1.0] - 2026-08-06

### Added

- Initial project scaffold: `src/` package layout, packaging (`hatchling` + `uv`),
  ruff, pytest, and smoke version test.
- No rate-limiter implementation yet.

[Unreleased]: https://github.com/luisgcss/starlette-ratelimiter/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/luisgcss/starlette-ratelimiter/releases/tag/v0.1.0
