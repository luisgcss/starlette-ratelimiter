"""Redis fixed-window rate limit backend."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable
from typing import Any, Protocol, cast

from asgi_ratelimiter.backends.base import HitResult
from asgi_ratelimiter.logging import get_logger

log = get_logger()

DEFAULT_REDIS_URL = "redis://localhost:6379/0"


class _RedisCommands(Protocol):
    def incr(self, name: str, amount: int = 1) -> Any: ...

    def expire(self, name: str, time: int) -> Any: ...

    def ttl(self, name: str) -> Any: ...


def _require_redis() -> Any:
    try:
        import redis
    except ImportError as exc:
        msg = (
            "Redis backend requires the 'redis' extra. "
            "Install with: pip install 'asgi-ratelimiter[redis]'"
        )
        raise ImportError(msg) from exc
    return redis


def _client_is_async(client: object) -> bool:
    return type(client).__module__.startswith("redis.asyncio")


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await cast(Awaitable[Any], value)
    return value


class RedisBackend:
    """Fixed-window limiter using Redis ``INCR`` + ``EXPIRE``.

    Accepts ``redis.asyncio`` clients (preferred) or sync ``redis.Redis`` /
    ``redis.cluster.RedisCluster`` (commands run via ``asyncio.to_thread``).

    Note: ``INCR`` and ``EXPIRE`` are separate commands; a process crash between
    them can leave a key without TTL until overwritten.
    """

    def __init__(
        self,
        redis: _RedisCommands | None = None,
        *,
        redis_class: type | None = None,
        redis_url: str = DEFAULT_REDIS_URL,
    ) -> None:
        _require_redis()
        if redis is not None:
            self._client: _RedisCommands = redis
            self._owns_client = False
        else:
            client_cls = redis_class
            if client_cls is None:
                from redis.asyncio import Redis as AsyncRedis

                client_cls = AsyncRedis
            self._client = client_cls.from_url(redis_url)
            self._owns_client = True

        self._async = _client_is_async(self._client)
        log.debug(
            "Redis backend ready async={} owns_client={}",
            self._async,
            self._owns_client,
        )

    async def close(self) -> None:
        """Close the client when this backend created it."""
        if not self._owns_client:
            return
        close = getattr(self._client, "aclose", None) or getattr(
            self._client, "close", None
        )
        if close is None:
            return
        result = close()
        if inspect.isawaitable(result):
            await result

    async def _incr(self, key: str) -> int:
        if self._async:
            return int(await _maybe_await(self._client.incr(key)))
        return int(await asyncio.to_thread(self._client.incr, key))

    async def _expire(self, key: str, seconds: int) -> None:
        if self._async:
            await _maybe_await(self._client.expire(key, seconds))
            return
        await asyncio.to_thread(self._client.expire, key, seconds)

    async def _ttl(self, key: str) -> int:
        if self._async:
            return int(await _maybe_await(self._client.ttl(key)))
        return int(await asyncio.to_thread(self._client.ttl, key))

    async def hit(
        self,
        key: str,
        *,
        limit: int,
        interval_seconds: int,
    ) -> HitResult:
        count = await self._incr(key)
        if count == 1:
            await self._expire(key, interval_seconds)

        allowed = count <= limit
        retry_after: int | None = None
        if not allowed:
            ttl = await self._ttl(key)
            retry_after = ttl if ttl > 0 else None

        log.debug(
            "hit key={} count={} limit={} allowed={} retry_after={}",
            key,
            count,
            limit,
            allowed,
            retry_after,
        )
        return HitResult(
            allowed=allowed,
            count=count,
            retry_after=retry_after,
        )
