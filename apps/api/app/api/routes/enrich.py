"""Compatibility wrapper for enrich routes.

Canonical implementation lives in app.domains.enrich.api.routes.
"""

from app.domains.enrich.api.routes import enrich_entity, router

__all__ = ["router", "enrich_entity"]