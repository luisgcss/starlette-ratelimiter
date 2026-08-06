"""Time interval helpers for rate limits."""

from __future__ import annotations

from typing import ClassVar


class Duration:
    """Immutable duration in seconds.

    Multiply unit constants to build intervals::

        Duration.MINUTE * 5  # 300 seconds
    """

    __slots__ = ("_seconds",)

    SECOND: ClassVar[Duration]
    MINUTE: ClassVar[Duration]
    HOUR: ClassVar[Duration]
    DAY: ClassVar[Duration]
    WEEK: ClassVar[Duration]

    def __init__(self, seconds: int) -> None:
        if not isinstance(seconds, int):
            msg = f"seconds must be int, got {type(seconds).__name__}"
            raise TypeError(msg)
        if seconds <= 0:
            msg = "seconds must be a positive integer"
            raise ValueError(msg)
        self._seconds = seconds

    @property
    def seconds(self) -> int:
        """Duration length in whole seconds."""
        return self._seconds

    def __mul__(self, other: int) -> Duration:
        if not isinstance(other, int):
            return NotImplemented
        if other <= 0:
            msg = "duration multiplier must be a positive integer"
            raise ValueError(msg)
        return Duration(self._seconds * other)

    def __rmul__(self, other: int) -> Duration:
        return self.__mul__(other)

    def __int__(self) -> int:
        return self._seconds

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Duration):
            return self._seconds == other._seconds
        return NotImplemented

    def __hash__(self) -> int:
        return hash((type(self), self._seconds))

    def __repr__(self) -> str:
        return f"Duration(seconds={self._seconds})"

    def __str__(self) -> str:
        return f"{self._seconds}s"


Duration.SECOND = Duration(1)
Duration.MINUTE = Duration(60)
Duration.HOUR = Duration(60 * 60)
Duration.DAY = Duration(60 * 60 * 24)
Duration.WEEK = Duration(60 * 60 * 24 * 7)
