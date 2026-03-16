"""Compatibility wrapper for deal routes.

Canonical implementation lives in app.domains.deals.api.routes.
"""

from app.domains.deals.api.routes import router

__all__ = ["router"]