"""Compatibility wrapper for price-quote routes.

Canonical implementation lives in app.domains.price_quotes.api.routes.
"""

from app.domains.price_quotes.api.routes import router

__all__ = ["router"]