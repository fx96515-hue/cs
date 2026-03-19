"""Compatibility wrapper for sentiment routes.

Canonical implementation lives in app.domains.sentiment.api.routes.
"""

from app.domains.sentiment.api.routes import router, settings

__all__ = ["router", "settings"]
