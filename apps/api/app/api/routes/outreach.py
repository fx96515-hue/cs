"""Compatibility wrapper for outreach API routes.

Canonical implementation lives in app.domains.outreach.api.routes.
"""

from app.domains.outreach.api.routes import router

__all__ = ["router"]
