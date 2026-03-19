"""Compatibility wrapper for dedup routes.

Canonical implementation lives in app.domains.dedup.api.routes.
"""

from app.domains.dedup.api.routes import router

__all__ = ["router"]
