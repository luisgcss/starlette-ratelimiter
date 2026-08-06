"""Rate limit configuration."""

from __future__ import annotations

from dataclasses import dataclass

from asgi_ratelimiter.duration import Duration


@dataclass(frozen=True, slots=True)
class Rate:
	"""How many calls are allowed within an interval.

	Example::

		Rate(limit=1, interval=Duration.MINUTE * 5)
	"""

	limit: int
	interval: Duration

	def __post_init__(self) -> None:
		if not isinstance(self.limit, int):
			msg = f"limit must be int, got {type(self.limit).__name__}"
			raise TypeError(msg)
		if self.limit < 1:
			msg = "limit must be >= 1"
			raise ValueError(msg)
		if not isinstance(self.interval, Duration):
			msg = f"interval must be Duration, got {type(self.interval).__name__}"
			raise TypeError(msg)
