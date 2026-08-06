"""Unit tests for Rate."""

import pytest

from asgi_ratelimiter import Duration, Rate


@pytest.mark.unit
class TestRate:
	def test_valid_rate(self) -> None:
		rate = Rate(limit=1, interval=Duration.MINUTE * 5)
		assert rate.limit == 1
		assert rate.interval.seconds == 300

	def test_rejects_invalid_limit(self) -> None:
		with pytest.raises(ValueError):
			Rate(limit=0, interval=Duration.SECOND)

	def test_rejects_non_int_limit(self) -> None:
		with pytest.raises(TypeError, match="limit must be int"):
			Rate(limit=1.5, interval=Duration.SECOND)  # type: ignore[arg-type]

	def test_rejects_invalid_interval_type(self) -> None:
		with pytest.raises(TypeError):
			Rate(limit=1, interval=60)  # type: ignore[arg-type]
