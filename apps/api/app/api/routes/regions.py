"""Compatibility wrapper for regions routes.

Canonical implementation lives in app.domains.regions.api.routes.
"""

from app.domains.regions.api.routes import router

__all__ = ["router"]
