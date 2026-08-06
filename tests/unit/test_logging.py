"""Unit tests for logging helpers."""

import pytest

from asgi_ratelimiter import configure_logging, set_level
from asgi_ratelimiter.logging import get_logger


@pytest.mark.unit
def test_configure_logging_and_set_level() -> None:
    configure_logging(level="DEBUG")
    set_level("WARNING")
    log = get_logger()
    log.warning("test warning")
