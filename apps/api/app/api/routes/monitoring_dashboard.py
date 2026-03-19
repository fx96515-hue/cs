"""Compatibility wrapper for monitoring dashboard routes.

Canonical implementation lives in app.domains.monitoring.api.routes.
"""

from app.domains.monitoring.api.routes import router

__all__ = ["router"]
