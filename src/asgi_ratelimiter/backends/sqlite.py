"""SQLite fixed-window rate limit backend."""

from __future__ import annotations

import asyncio
import sqlite3
import threading
import time
import weakref
from pathlib import Path

from asgi_ratelimiter.backends.base import HitResult
from asgi_ratelimiter.logging import get_logger

log = get_logger()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS rate_limits (
    key TEXT PRIMARY KEY NOT NULL,
    count INTEGER NOT NULL,
    expires_at REAL NOT NULL
)
"""


class SQLiteBackend:
    """Fixed-window limiter stored in SQLite (stdlib ``sqlite3``).

    Uses a single sync connection guarded by a thread lock, invoked via
    ``asyncio.to_thread`` so ASGI handlers stay non-blocking without
    aiosqlite worker threads that can hang process exit.
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._db_path = str(db_path)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            self._db_path,
            check_same_thread=False,
            timeout=30,
        )
        self._conn.execute("PRAGMA journal_mode=DELETE")
        self._conn.execute(_SCHEMA)
        self._conn.commit()
        self._closed = False
        self._finalizer = weakref.finalize(
            self,
            _close_connection,
            self._conn,
            self._lock,
        )
        log.debug("SQLite backend ready path={}", self._db_path)

    async def close(self) -> None:
        """Close the underlying SQLite connection."""
        await asyncio.to_thread(self._close_sync)

    def _close_sync(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._finalizer.detach()
            self._conn.close()

    async def hit(
        self,
        key: str,
        *,
        limit: int,
        interval_seconds: int,
    ) -> HitResult:
        return await asyncio.to_thread(
            self._hit_sync,
            key,
            limit,
            interval_seconds,
        )

    def _hit_sync(self, key: str, limit: int, interval_seconds: int) -> HitResult:
        now = time.time()
        with self._lock:
            if self._closed:
                msg = "SQLiteBackend is closed"
                raise RuntimeError(msg)

            row = self._conn.execute(
                "SELECT count, expires_at FROM rate_limits WHERE key = ?",
                (key,),
            ).fetchone()

            if row is None or float(row[1]) <= now:
                count = 1
                expires_at = now + interval_seconds
                self._conn.execute(
                    """
                    INSERT INTO rate_limits (key, count, expires_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        count = excluded.count,
                        expires_at = excluded.expires_at
                    """,
                    (key, count, expires_at),
                )
            else:
                count = int(row[0]) + 1
                expires_at = float(row[1])
                self._conn.execute(
                    "UPDATE rate_limits SET count = ? WHERE key = ?",
                    (count, key),
                )

            self._conn.commit()

        retry_after = max(0, int(expires_at - now))
        allowed = count <= limit
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
            retry_after=retry_after if not allowed else None,
        )


def _close_connection(conn: sqlite3.Connection, lock: threading.Lock) -> None:
    with lock:
        try:
            conn.close()
        except Exception:  # noqa: BLE001 - best-effort finalizer
            pass
