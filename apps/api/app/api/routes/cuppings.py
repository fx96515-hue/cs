"""Compatibility wrapper for cupping routes.

Canonical implementation lives in app.domains.cuppings.api.routes.
"""

from app.domains.cuppings.api.routes import router

__all__ = ["router"]
