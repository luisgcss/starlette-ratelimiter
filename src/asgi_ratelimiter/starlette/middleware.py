"""Starlette rate limit middleware."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING

from asgi_ratelimiter.logging import get_logger
from asgi_ratelimiter.rate import Rate

if TYPE_CHECKING:
	from asgi_ratelimiter.backends.base import StorageBackend

log = get_logger()

try:
	from starlette.middleware.base import BaseHTTPMiddleware
	from starlette.requests import Request
	from starlette.responses import JSONResponse, Response
	from starlette.types import ASGIApp
except ImportError as exc:  # pragma: no cover
	msg = (
		"Starlette integration requires the 'starlette' extra. "
		"Install with: pip install 'asgi-ratelimiter[starlette]'"
	)
	raise ImportError(msg) from exc


def _default_identifier(request: Request) -> str:
	if request.client is not None and request.client.host:
		return request.client.host
	return "default"


class RateLimitMiddleware(BaseHTTPMiddleware):
	"""Reject requests that exceed ``rate`` for a resolved client key.

	Pass ``backend=RedisBackend(redis=...)`` for Redis, or omit ``backend``
	to use the default SQLite store (``db_path``).
	"""

	def __init__(
		self,
		app: ASGIApp,
		*,
		rate: Rate,
		identifier: Callable[[Request], str] | None = None,
		backend: StorageBackend | None = None,
		db_path: str | Path = ":memory:",
		key_prefix: str = "asgi-ratelimiter",
	) -> None:
		super().__init__(app)
		if not isinstance(rate, Rate):
			msg = f"rate must be Rate, got {type(rate).__name__}"
			raise TypeError(msg)
		if identifier is not None and not callable(identifier):
			msg = "identifier must be callable"
			raise TypeError(msg)
		if not key_prefix:
			msg = "key_prefix must be a non-empty string"
			raise ValueError(msg)

		self.rate = rate
		self.identifier = identifier or _default_identifier
		if backend is None:
			from asgi_ratelimiter.backends.sqlite import SQLiteBackend

			self.backend: StorageBackend = SQLiteBackend(db_path)
		else:
			self.backend = backend
		self.key_prefix = key_prefix

	async def dispatch(
		self,
		request: Request,
		call_next: Callable[[Request], Awaitable[Response]],
	) -> Response:
		identity = self.identifier(request)
		key = f"{self.key_prefix}:{identity}"
		result = await self.backend.hit(
			key,
			limit=self.rate.limit,
			interval_seconds=self.rate.interval.seconds,
		)
		if not result.allowed:
			log.warning(
				"rate limit exceeded key={} count={} limit={} retry_after={}",
				key,
				result.count,
				self.rate.limit,
				result.retry_after,
			)
			headers: dict[str, str] = {}
			if result.retry_after is not None:
				headers["Retry-After"] = str(result.retry_after)
			return JSONResponse(
				{"detail": "Rate limit exceeded"},
				status_code=429,
				headers=headers,
			)
		log.debug(
			"rate limit allowed key={} count={} limit={}",
			key,
			result.count,
			self.rate.limit,
		)
		return await call_next(request)
