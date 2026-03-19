"""Compatibility wrapper for knowledge-base routes.

Canonical implementation lives in app.domains.kb.api.routes.
"""

from app.domains.kb.api.routes import router

__all__ = ["router"]
