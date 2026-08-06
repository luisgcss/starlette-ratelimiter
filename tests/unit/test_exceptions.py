"""Unit tests for exceptions."""

import pytest

from asgi_ratelimiter import RateLimiterError, RateLimitExceeded


@pytest.mark.unit
class TestExceptions:
    def test_rate_limit_exceeded_attrs(self) -> None:
        err = RateLimitExceeded(limit=5, retry_after=12)
        assert isinstance(err, RateLimiterError)
        assert str(err) == "Rate limit exceeded"
        assert err.limit == 5
        assert err.retry_after == 12

    def test_custom_message(self) -> None:
        err = RateLimitExceeded("too many", limit=1, retry_after=None)
        assert str(err) == "too many"
        assert err.retry_after is None
