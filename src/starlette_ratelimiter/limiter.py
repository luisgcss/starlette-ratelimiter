"""Redis-backed fixed-window rate limiter."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from redis import Redis
from redis.cluster import RedisCluster

from starlette_ratelimiter.exceptions import RateLimitExceeded
from starlette_ratelimiter.rate import Rate

Identifier = Callable[[], str]

DEFAULT_REDIS_URL = "redis://localhost:6379/0"
DEFAULT_KEY_PREFIX = "starlette-ratelimiter"


@runtime_checkable
class RedisClient(Protocol):
    """Minimal Redis surface used by :class:`RateLimiter`."""

    def incr(self, name: str, amount: int = 1) -> int: ...

    def expire(self, name: str, time: int) -> bool: ...

    def ttl(self, name: str) -> int: ...


def default_identifier() -> str:
    """Default key identity when no identifier callback is provided."""
    return "default"


def _build_redis(
    *,
    redis: Redis | RedisCluster | None,
    redis_class: type[Redis] | type[RedisCluster] | None,
    redis_url: str,
) -> Redis | RedisCluster:
    if redis is not None:
        return redis
    client_cls: type[Redis] | type[RedisCluster] = redis_class or Redis
    return client_cls.from_url(redis_url)


class RateLimiter:
    """Fixed-window rate limiter backed by Redis or Redis Cluster.

    Example::

        limiter = RateLimiter(
            rate=Rate(limit=1, interval=Duration.MINUTE * 5),
            identifier=my_function_which_returns_an_string,
            redis=redis_client,
        )
        if not limiter.hit():
            ...
    """

    def __init__(
        self,
        *,
        rate: Rate,
        identifier: Identifier | None = None,
        redis: Redis | RedisCluster | None = None,
        redis_class: type[Redis] | type[RedisCluster] | None = None,
        redis_url: str = DEFAULT_REDIS_URL,
        key_prefix: str = DEFAULT_KEY_PREFIX,
    ) -> None:
        if not isinstance(rate, Rate):
            msg = f"rate must be Rate, got {type(rate).__name__}"
            raise TypeError(msg)
        if identifier is not None and not callable(identifier):
            msg = "identifier must be callable"
            raise TypeError(msg)
        if not key_prefix:
            msg = "key_prefix must be a non-empty string"
            raise ValueError(msg)

        self._rate = rate
        self._identifier: Identifier = identifier or default_identifier
        self._key_prefix = key_prefix
        self._redis: RedisClient = _build_redis(
            redis=redis,
            redis_class=redis_class,
            redis_url=redis_url,
        )

    @property
    def rate(self) -> Rate:
        return self._rate

    @property
    def redis(self) -> RedisClient:
        return self._redis

    def key(self) -> str:
        """Build the Redis key for the current identifier."""
        identity = self._identifier()
        if not isinstance(identity, str) or not identity:
            msg = "identifier must return a non-empty string"
            raise ValueError(msg)
        return f"{self._key_prefix}:{identity}"

    def hit(self) -> bool:
        """Record one call. Return ``True`` if allowed, ``False`` if limited."""
        redis_key = self.key()
        count = int(self._redis.incr(redis_key))
        if count == 1:
            self._redis.expire(redis_key, self._rate.interval.seconds)
        return count <= self._rate.limit

    def hit_or_raise(self) -> None:
        """Record one call, raise :class:`RateLimitExceeded` when limited."""
        redis_key = self.key()
        count = int(self._redis.incr(redis_key))
        if count == 1:
            self._redis.expire(redis_key, self._rate.interval.seconds)
        if count > self._rate.limit:
            retry_after = self._redis.ttl(redis_key)
            raise RateLimitExceeded(
                limit=self._rate.limit,
                retry_after=retry_after if retry_after and retry_after > 0 else None,
            )
