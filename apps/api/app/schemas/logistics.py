"""Compatibility wrapper for logistics schemas.

Canonical implementation lives in app.domains.logistics.schemas.logistics.
"""

from app.domains.logistics.schemas.logistics import (
    LandedCostRequest,
    LandedCostResponse,
)

__all__ = ["LandedCostRequest", "LandedCostResponse"]
