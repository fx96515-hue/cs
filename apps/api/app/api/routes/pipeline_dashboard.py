"""Compatibility wrapper for pipeline dashboard routes.

Canonical implementation lives in app.domains.pipeline.api.routes.
"""

from app.domains.pipeline.api.routes import router

__all__ = ["router"]
