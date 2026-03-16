"""Compatibility wrapper for feature dashboard routes.

Canonical implementation lives in app.domains.features.api.routes.
"""

from app.domains.features.api.routes import router

__all__ = ["router"]
