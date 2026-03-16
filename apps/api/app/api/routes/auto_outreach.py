"""Compatibility wrapper for auto-outreach routes.

Canonical implementation lives in app.domains.auto_outreach.api.routes.
"""

from app.domains.auto_outreach.api.routes import auto_outreach, router

__all__ = ["router", "auto_outreach"]