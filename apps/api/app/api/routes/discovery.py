"""Compatibility wrapper for discovery routes.

Canonical implementation lives in app.domains.discovery.api.routes.
"""

from app.domains.discovery.api.routes import SeedRequest, celery, router

__all__ = ["router", "SeedRequest", "celery"]