"""Library logging via loguru."""

from __future__ import annotations

import sys
from typing import Any

from loguru import logger

_LIBRARY = "asgi_ratelimiter"
_configured = False
_handler_id: int | None = None

logger.disable(_LIBRARY)


def configure_logging(level: str | int = "INFO", **sink_options: Any) -> None:
	"""Enable and configure asgi-ratelimiter logs.

	Parameters
	----------
	level:
		Loguru level name or numeric level (e.g. ``"DEBUG"``, ``10``).
	sink_options:
		Extra keyword arguments forwarded to ``logger.add`` (e.g. ``format``).
	"""
	global _configured, _handler_id

	logger.enable(_LIBRARY)
	if _handler_id is not None:
		logger.remove(_handler_id)

	options: dict[str, Any] = {
		"sink": sys.stderr,
		"level": level,
		"filter": lambda record: record["name"].startswith(_LIBRARY),
		"enqueue": False,
	}
	options.update(sink_options)
	_handler_id = logger.add(**options)
	_configured = True


def get_logger():
	"""Return the bound library logger."""
	return logger.bind(library=_LIBRARY)


def set_level(level: str | int) -> None:
	"""Reconfigure logging at ``level`` (enables logging if needed)."""
	configure_logging(level=level)
