"""Compatibility wrapper for margin schemas.

Canonical implementation lives in app.domains.margins.schemas.margin.
"""

from app.domains.margins.schemas.margin import (
    MarginCalcRequest,
    MarginCalcResult,
    MarginRunOut,
)

__all__ = ["MarginCalcRequest", "MarginCalcResult", "MarginRunOut"]
