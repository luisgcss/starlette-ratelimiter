"""Unit tests for Duration."""

import pytest

from asgi_ratelimiter import Duration


@pytest.mark.unit
class TestDuration:
    def test_unit_constants(self) -> None:
        assert Duration.SECOND.seconds == 1
        assert Duration.MINUTE.seconds == 60
        assert Duration.HOUR.seconds == 3600
        assert Duration.DAY.seconds == 86400
        assert Duration.WEEK.seconds == 604800

    def test_multiply(self) -> None:
        assert (Duration.MINUTE * 5).seconds == 300
        assert (5 * Duration.MINUTE).seconds == 300

    def test_multiply_non_int_returns_not_implemented(self) -> None:
        assert Duration.SECOND.__mul__(2.5) is NotImplemented  # type: ignore[arg-type]

    def test_rejects_non_positive(self) -> None:
        with pytest.raises(ValueError):
            Duration(0)
        with pytest.raises(ValueError):
            Duration(-1)
        with pytest.raises(ValueError):
            Duration.SECOND * 0

    def test_rejects_non_int(self) -> None:
        with pytest.raises(TypeError):
            Duration(1.5)  # type: ignore[arg-type]

    def test_equality_and_hash(self) -> None:
        assert Duration.MINUTE * 2 == Duration(120)
        assert hash(Duration(10)) == hash(Duration(10))
        assert Duration(1).__eq__("nope") is NotImplemented

    def test_int_repr_str(self) -> None:
        d = Duration(42)
        assert int(d) == 42
        assert repr(d) == "Duration(seconds=42)"
        assert str(d) == "42s"
