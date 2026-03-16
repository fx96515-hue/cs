"""Compatibility wrapper for health routes.

Canonical implementation lives in app.domains.health.api.health_routes.
"""

from app.domains.health.api.health_routes import redis_lib, router

__all__ = ["router", "redis_lib"]