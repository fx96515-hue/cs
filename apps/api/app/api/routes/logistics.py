"""Compatibility wrapper for logistics routes.

Canonical implementation lives in app.domains.logistics.api.routes.
"""

from app.domains.logistics.api.routes import router

__all__ = ["router"]
