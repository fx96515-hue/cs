"""Compatibility wrapper for data-quality routes.

Canonical implementation lives in app.domains.data_quality.api.routes.
"""

from app.domains.data_quality.api.routes import recompute_entity_flags, router

__all__ = ["router", "recompute_entity_flags"]