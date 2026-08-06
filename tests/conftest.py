"""Shared pytest fixtures for asgi-ratelimiter."""

from __future__ import annotations

import typing

# Python 3.14.0b4 lacks typing._eval_type(prefer_fwd_module=...).
# pydantic/FastAPI import requires that kwarg.
_orig_eval_type = typing._eval_type


def _eval_type_compat(*args, prefer_fwd_module=None, **kwargs):
    return _orig_eval_type(*args, **kwargs)


typing._eval_type = _eval_type_compat  # type: ignore[assignment]
