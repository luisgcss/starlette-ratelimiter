"""Storage backend protocol and result types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class HitResult:
	"""Outcome of a rate-limit hit attempt."""

	allowed: bool
	count: int
	retry_after: int | None = None


@runtime_checkable
class StorageBackend(Protocol):
	"""Async storage used by framework rate limiters."""

	async def hit(
		self,
		key: str,
		*,
		limit: int,
		interval_seconds: int,
	) -> HitResult:
		"""Record one call for ``key`` within a fixed window."""
		...  # pragma: no cover
