"""Compatibility wrapper for source routes.

Canonical implementation lives in app.domains.sources.api.routes.
"""

from app.domains.sources.api.routes import router

__all__ = ["router"]