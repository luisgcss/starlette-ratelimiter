"""Unit tests for RateLimiter."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from redis import Redis
from redis.cluster import RedisCluster

from starlette_ratelimiter import Duration, Rate, RateLimiter, RateLimitExceeded


def _mock_redis(*, counts: list[int], ttl: int = 42) -> MagicMock:
    client = MagicMock()
    client.incr.side_effect = counts
    client.ttl.return_value = ttl
    return client


@pytest.mark.unit
class TestRateLimiter:
    def test_hit_allows_under_limit(self) -> None:
        redis = _mock_redis(counts=[1])
        limiter = RateLimiter(
            rate=Rate(limit=2, interval=Duration.MINUTE),
            identifier=lambda: "user:1",
            redis=redis,
        )

        assert limiter.hit() is True
        redis.incr.assert_called_once_with("starlette-ratelimiter:user:1")
        redis.expire.assert_called_once_with("starlette-ratelimiter:user:1", 60)

    def test_hit_blocks_over_limit(self) -> None:
        redis = _mock_redis(counts=[3])
        limiter = RateLimiter(
            rate=Rate(limit=2, interval=Duration.SECOND * 10),
            identifier=lambda: "user:1",
            redis=redis,
        )

        assert limiter.hit() is False
        redis.expire.assert_not_called()

    def test_default_identifier(self) -> None:
        redis = _mock_redis(counts=[1])
        limiter = RateLimiter(
            rate=Rate(limit=1, interval=Duration.MINUTE * 5),
            redis=redis,
        )

        assert limiter.key() == "starlette-ratelimiter:default"
        assert limiter.hit() is True

    def test_custom_identifier(self) -> None:
        redis = _mock_redis(counts=[1])
        limiter = RateLimiter(
            rate=Rate(limit=1, interval=Duration.MINUTE * 5),
            identifier=lambda: "ip:10.0.0.1",
            redis=redis,
        )

        assert limiter.key() == "starlette-ratelimiter:ip:10.0.0.1"

    def test_hit_or_raise(self) -> None:
        redis = _mock_redis(counts=[2], ttl=17)
        limiter = RateLimiter(
            rate=Rate(limit=1, interval=Duration.MINUTE),
            identifier=lambda: "user:1",
            redis=redis,
        )

        with pytest.raises(RateLimitExceeded) as exc_info:
            limiter.hit_or_raise()

        assert exc_info.value.limit == 1
        assert exc_info.value.retry_after == 17

    def test_instantiate_redis_from_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        created: dict[str, Any] = {}

        class FakeRedis:
            @classmethod
            def from_url(cls, url: str, **_kwargs: Any) -> MagicMock:
                created["url"] = url
                created["cls"] = cls
                return _mock_redis(counts=[1])

        monkeypatch.setattr("starlette_ratelimiter.limiter.Redis", FakeRedis)

        limiter = RateLimiter(
            rate=Rate(limit=1, interval=Duration.SECOND),
            redis_url="redis://example:6379/2",
        )

        assert created["url"] == "redis://example:6379/2"
        assert created["cls"] is FakeRedis
        assert limiter.hit() is True

    def test_instantiate_redis_cluster_class(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        created: dict[str, Any] = {}

        class FakeCluster:
            @classmethod
            def from_url(cls, url: str, **_kwargs: Any) -> MagicMock:
                created["cls"] = cls
                return _mock_redis(counts=[1])

        monkeypatch.setattr(
            "starlette_ratelimiter.limiter.RedisCluster",
            FakeCluster,
        )

        limiter = RateLimiter(
            rate=Rate(limit=1, interval=Duration.SECOND),
            redis_class=FakeCluster,  # type: ignore[arg-type]
        )

        assert created["cls"] is FakeCluster
        assert isinstance(limiter.redis, MagicMock)

    def test_rejects_empty_identifier_result(self) -> None:
        redis = _mock_redis(counts=[1])
        limiter = RateLimiter(
            rate=Rate(limit=1, interval=Duration.SECOND),
            identifier=lambda: "",
            redis=redis,
        )

        with pytest.raises(ValueError):
            limiter.key()

    def test_accepts_redis_and_cluster_types(self) -> None:
        assert issubclass(Redis, object)
        assert issubclass(RedisCluster, object)
