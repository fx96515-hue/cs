"""Compatibility wrapper for news routes.

Canonical implementation lives in app.domains.news.api.routes.
"""

from app.domains.news.api.routes import router

__all__ = ["router"]
