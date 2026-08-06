"""Public exception hierarchy."""

from __future__ import annotations


class RateLimiterError(Exception):
	"""Base error for asgi-ratelimiter."""


class RateLimitExceeded(RateLimiterError):  # noqa: N818
	"""Raised when a caller exceeds the configured rate."""

	def __init__(
		self,
		message: str = "Rate limit exceeded",
		*,
		limit: int,
		retry_after: int | None = None,
	) -> None:
		super().__init__(message)
		self.limit = limit
		self.retry_after = retry_after
