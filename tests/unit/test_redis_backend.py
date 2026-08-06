"""Unit tests for RedisBackend."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from asgi_ratelimiter.backends.redis import RedisBackend


class _AsyncRedisStub:
	__module__ = "redis.asyncio.client"

	def __init__(self, *, counts: list[int], ttl: int = 42) -> None:
		self.incr = AsyncMock(side_effect=counts)
		self.expire = AsyncMock(return_value=True)
		self.ttl = AsyncMock(return_value=ttl)
		self.aclose = AsyncMock()


class _SyncRedisStub:
	__module__ = "redis.client"

	def __init__(self, *, counts: list[int], ttl: int = 42) -> None:
		self.incr = MagicMock(side_effect=counts)
		self.expire = MagicMock(return_value=True)
		self.ttl = MagicMock(return_value=ttl)
		self.close = MagicMock()


@pytest.mark.unit
@pytest.mark.asyncio
class TestRedisBackendAsync:
	async def test_allows_under_limit_and_sets_expire(self) -> None:
		client = _AsyncRedisStub(counts=[1])
		backend = RedisBackend(redis=client)
		result = await backend.hit("k", limit=2, interval_seconds=60)
		assert result.allowed is True
		assert result.count == 1
		client.incr.assert_awaited_once_with("k")
		client.expire.assert_awaited_once_with("k", 60)

	async def test_blocks_over_limit_with_retry_after(self) -> None:
		client = _AsyncRedisStub(counts=[3], ttl=17)
		backend = RedisBackend(redis=client)
		result = await backend.hit("k", limit=2, interval_seconds=60)
		assert result.allowed is False
		assert result.count == 3
		assert result.retry_after == 17
		client.expire.assert_not_called()
		client.ttl.assert_awaited_once_with("k")

	async def test_negative_ttl_becomes_none(self) -> None:
		client = _AsyncRedisStub(counts=[2], ttl=-1)
		backend = RedisBackend(redis=client)
		result = await backend.hit("k", limit=1, interval_seconds=30)
		assert result.allowed is False
		assert result.retry_after is None

	async def test_close_owned_client(self) -> None:
		created = _AsyncRedisStub(counts=[1])

		class FakeAsyncRedis:
			@classmethod
			def from_url(cls, url: str, **_kwargs: object) -> _AsyncRedisStub:
				assert url == "redis://example:6379/0"
				return created

		with patch("redis.asyncio.Redis", FakeAsyncRedis):
			backend = RedisBackend(redis_url="redis://example:6379/0")
		await backend.close()
		created.aclose.assert_awaited_once()

	async def test_close_does_not_close_injected_client(self) -> None:
		client = _AsyncRedisStub(counts=[1])
		backend = RedisBackend(redis=client)
		await backend.close()
		client.aclose.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
class TestRedisBackendSync:
	async def test_sync_client_via_to_thread(self) -> None:
		client = _SyncRedisStub(counts=[1, 2])
		backend = RedisBackend(redis=client)
		first = await backend.hit("k", limit=2, interval_seconds=10)
		second = await backend.hit("k", limit=2, interval_seconds=10)
		assert first.allowed is True
		assert first.count == 1
		assert second.allowed is True
		assert second.count == 2
		assert client.expire.call_count == 1
		client.expire.assert_called_with("k", 10)

	async def test_sync_over_limit_reads_ttl(self) -> None:
		client = _SyncRedisStub(counts=[2], ttl=9)
		backend = RedisBackend(redis=client)
		result = await backend.hit("k", limit=1, interval_seconds=30)
		assert result.allowed is False
		assert result.retry_after == 9
		client.ttl.assert_called_once_with("k")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redis_class_and_close_variants() -> None:
	created = _SyncRedisStub(counts=[1])

	class FakeSyncRedis:
		@classmethod
		def from_url(cls, url: str, **_kwargs: object) -> _SyncRedisStub:
			return created

	backend = RedisBackend(
		redis_class=FakeSyncRedis,
		redis_url="redis://localhost:6379/1",
	)
	assert backend._owns_client is True
	await backend.hit("k", limit=1, interval_seconds=5)
	await backend.close()
	created.close.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_close_without_close_methods() -> None:
	class BareAsync:
		__module__ = "redis.asyncio.client"

		@classmethod
		def from_url(cls, url: str, **_kwargs: object) -> BareAsync:
			return cls()

	backend = RedisBackend(redis_class=BareAsync)
	await backend.close()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_client_returning_plain_values() -> None:
	"""Some wrappers look async by module but return plain values."""

	class PlainAsyncRedis:
		__module__ = "redis.asyncio.client"

		def __init__(self) -> None:
			self.incr = MagicMock(return_value=1)
			self.expire = MagicMock(return_value=True)
			self.ttl = MagicMock(return_value=3)

	client = PlainAsyncRedis()
	backend = RedisBackend(redis=client)
	result = await backend.hit("k", limit=1, interval_seconds=10)
	assert result.allowed is True
	assert result.count == 1


@pytest.mark.unit
def test_import_error_without_redis(monkeypatch: pytest.MonkeyPatch) -> None:
	import builtins

	real_import = builtins.__import__

	def _fake_import(name: str, *args: object, **kwargs: object):
		if name == "redis" or name.startswith("redis."):
			raise ImportError("no redis")
		return real_import(name, *args, **kwargs)

	monkeypatch.setattr(builtins, "__import__", _fake_import)
	with pytest.raises(ImportError, match=r"asgi-ratelimiter\[redis\]"):
		RedisBackend(redis=SimpleNamespace())
