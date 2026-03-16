"""Compatibility wrapper for logistics service.

Canonical implementation lives in app.domains.logistics.services.costs.
"""

from app.domains.logistics.services.costs import (
    DEFAULT_USD_EUR,
    _latest_usd_eur,
    calc_landed_cost,
)

__all__ = ["DEFAULT_USD_EUR", "_latest_usd_eur", "calc_landed_cost"]