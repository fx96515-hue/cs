"""Compatibility wrapper for reports routes.

Canonical implementation lives in app.domains.reports.api.routes.
"""

from app.domains.reports.api.routes import router

__all__ = ["router"]
