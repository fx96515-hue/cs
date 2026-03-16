"""Compatibility wrapper for margins service.

Canonical implementation lives in app.domains.margins.services.calculator.
"""

from app.domains.margins.services.calculator import calc_margin

__all__ = ["calc_margin"]