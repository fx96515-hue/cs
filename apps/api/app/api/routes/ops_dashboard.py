"""Compatibility wrapper for ops dashboard routes.

Canonical implementation lives in app.domains.ops.api.routes.
"""

from app.domains.ops.api.routes import router

__all__ = ["router"]
