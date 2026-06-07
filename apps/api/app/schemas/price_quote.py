"""Compatibility wrapper for price-quote schemas.

Canonical implementation lives in app.domains.price_quotes.schemas.price_quote.
"""

from app.domains.price_quotes.schemas.price_quote import (
    PriceQuoteCreate,
    PriceQuoteOut,
    PriceQuoteUpdate,
    VALID_CURRENCIES,
)

__all__ = [
    "VALID_CURRENCIES",
    "PriceQuoteCreate",
    "PriceQuoteUpdate",
    "PriceQuoteOut",
]
