"""FastAPI Depends-compatible rate limiter."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from asgi_ratelimiter.backends.base import StorageBackend
from asgi_ratelimiter.logging import get_logger
from asgi_ratelimiter.rate import Rate

if TYPE_CHECKING:
	from starlette.requests import Request

try:
	from fastapi import HTTPException as _HTTPException
	from starlette.requests import Request as _Request
except ImportError:  # pragma: no cover
	_HTTPException = None  # type: ignore[misc, assignment]
	_Request = None  # type: ignore[misc, assignment]

Request = _Request  # type: ignore[misc]

log = get_logger()


def _default_identifier(request: Request) -> str:
	client = request.client
	if client is None:
		return "default"
	return client.host or "default"


class RateLimiter:
	"""Async FastAPI dependency that enforces a fixed-window rate limit.

	Use with ``Depends(RateLimiter(...))`` at app or route level.

	Pass ``backend=RedisBackend(redis=...)`` for Redis, or omit ``backend``
	to use the default SQLite store (``db_path``).
	"""

	def __init__(
		self,
		rate: Rate,
		*,
		identifier: Callable[[Request], str] | None = None,
		backend: StorageBackend | None = None,
		db_path: str | Path = ":memory:",
		key_prefix: str = "asgi-ratelimiter",
	) -> None:
		if _HTTPException is None or _Request is None:
			msg = (
				"FastAPI integration requires the 'fastapi' extra. "
				"Install with: pip install 'asgi-ratelimiter[fastapi]'"
			)
			raise ImportError(msg)

		if not isinstance(rate, Rate):
			msg = f"rate must be Rate, got {type(rate).__name__}"
			raise TypeError(msg)
		if identifier is not None and not callable(identifier):
			msg = "identifier must be callable"
			raise TypeError(msg)

		self._http_exception = _HTTPException
		self.rate = rate
		self.identifier: Callable[[Request], str] = (
			identifier if identifier is not None else _default_identifier
		)
		self.key_prefix = key_prefix

		if backend is None:
			from asgi_ratelimiter.backends.sqlite import SQLiteBackend

			self.backend: StorageBackend = SQLiteBackend(db_path)
		else:
			self.backend = backend

	async def __call__(self, request: Request) -> None:
		key = f"{self.key_prefix}:{self.identifier(request)}"
		result = await self.backend.hit(
			key,
			limit=self.rate.limit,
			interval_seconds=self.rate.interval.seconds,
		)
		if result.allowed:
			log.debug(
				"rate limit allowed key={} count={}/{}",
				key,
				result.count,
				self.rate.limit,
			)
			return

		log.warning(
			"rate limit exceeded key={} count={} retry_after={}",
			key,
			result.count,
			result.retry_after,
		)
		headers = (
			{"Retry-After": str(result.retry_after)}
			if result.retry_after is not None
			else None
		)
		raise self._http_exception(
			status_code=429,
			detail="Rate limit exceeded",
			headers=headers,
		)
