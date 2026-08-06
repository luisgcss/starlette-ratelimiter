"""Starlette integration for asgi-ratelimiter."""

from asgi_ratelimiter.starlette.middleware import RateLimitMiddleware

__all__ = ["RateLimitMiddleware"]
