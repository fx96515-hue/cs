"""Compatibility wrapper for data-quality service.

Canonical implementation lives in app.domains.data_quality.services.flags.
"""

from app.domains.data_quality.services.flags import (
    recompute_entity_flags,
    resolve_entity_flags,
)

__all__ = ["recompute_entity_flags", "resolve_entity_flags"]