"""Compatibility wrapper for cupping schemas.

Canonical implementation lives in app.domains.cuppings.schemas.cupping.
"""

from app.domains.cuppings.schemas.cupping import CuppingCreate, CuppingOut

__all__ = ["CuppingCreate", "CuppingOut"]