"""Unit tests for SQLite backend."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from asgi_ratelimiter.backends import sqlite as sqlite_mod
from asgi_ratelimiter.backends.sqlite import SQLiteBackend


@pytest.mark.unit
@pytest.mark.asyncio
class TestSQLiteBackend:
    async def test_allows_under_limit(self) -> None:
        backend = SQLiteBackend(":memory:")
        try:
            first = await backend.hit("k", limit=2, interval_seconds=60)
            second = await backend.hit("k", limit=2, interval_seconds=60)
            assert first.allowed is True
            assert first.count == 1
            assert second.allowed is True
            assert second.count == 2
        finally:
            await backend.close()

    async def test_blocks_over_limit(self) -> None:
        backend = SQLiteBackend(":memory:")
        try:
            await backend.hit("k", limit=1, interval_seconds=60)
            denied = await backend.hit("k", limit=1, interval_seconds=60)
            assert denied.allowed is False
            assert denied.count == 2
            assert denied.retry_after is not None
            assert denied.retry_after >= 0
        finally:
            await backend.close()

    async def test_separate_keys(self) -> None:
        backend = SQLiteBackend(":memory:")
        try:
            a = await backend.hit("a", limit=1, interval_seconds=60)
            b = await backend.hit("b", limit=1, interval_seconds=60)
            assert a.allowed is True
            assert b.allowed is True
        finally:
            await backend.close()

    async def test_window_reset_after_expiry(self) -> None:
        backend = SQLiteBackend(":memory:")
        try:
            first = await backend.hit("k", limit=1, interval_seconds=1)
            assert first.allowed is True
            # Force expiry by rewriting expires_at in the past.
            backend._conn.execute(
                "UPDATE rate_limits SET expires_at = 0 WHERE key = ?",
                ("k",),
            )
            backend._conn.commit()
            again = await backend.hit("k", limit=1, interval_seconds=60)
            assert again.allowed is True
            assert again.count == 1
        finally:
            await backend.close()

    async def test_close_is_idempotent_and_blocks_hit(self) -> None:
        backend = SQLiteBackend(":memory:")
        await backend.close()
        await backend.close()
        with pytest.raises(RuntimeError, match="closed"):
            await backend.hit("k", limit=1, interval_seconds=60)


@pytest.mark.unit
def test_finalizer_swallows_close_errors() -> None:
    conn = MagicMock()
    conn.close.side_effect = OSError("boom")
    lock = MagicMock()
    lock.__enter__ = MagicMock(return_value=None)
    lock.__exit__ = MagicMock(return_value=False)
    sqlite_mod._close_connection(conn, lock)
    conn.close.assert_called_once()
