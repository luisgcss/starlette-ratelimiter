"""Smoke tests for package metadata."""

import pytest

from fast_ratelimiter import __version__


@pytest.mark.unit
def test_version() -> None:
    assert __version__ == "0.1.0"
