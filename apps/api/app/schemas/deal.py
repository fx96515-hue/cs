"""Compatibility wrapper for deal schemas.

Canonical implementation lives in app.domains.deals.schemas.deal.
"""

from app.domains.deals.schemas.deal import (
    DealCreate,
    DealOut,
    DealUpdate,
    VALID_CURRENCIES,
    VALID_STATUSES,
)

__all__ = [
    "VALID_CURRENCIES",
    "VALID_STATUSES",
    "DealCreate",
    "DealUpdate",
    "DealOut",
]