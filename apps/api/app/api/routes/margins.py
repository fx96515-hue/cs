"""Compatibility wrapper for margins routes.

Canonical implementation lives in app.domains.margins.api.routes.
"""

from app.domains.margins.api.routes import router

__all__ = ["router"]
