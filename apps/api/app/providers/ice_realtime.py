"""ICE Coffee C Futures realtime price provider.

Uses Twelve Data (https://twelvedata.com/) as a free alternative to the
native ICE WebSocket feed.  The symbol ``KC1!`` maps to the Coffee C
Arabica front-month futures contract traded on ICE.

Fallback chain (used when the realtime feed is enabled):
1. Twelve Data REST API (requires TWELVE_DATA_API_KEY)
2. Yahoo Finance (KC=F) – existing provider, no API key needed

If both sources fail, this module returns ``None`` so that the normal
fallback chain in ``coffee_prices.py`` can continue to operate.

The module is intentionally import-safe: it never raises at module level,
so the normal fallback chain in ``coffee_prices.py`` continues to work
even when the feature flag is off.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

import httpx
import structlog

from app.providers.coffee_prices import CoffeeQuote

log = structlog.get_logger()

# Twelve Data REST endpoint
_TWELVE_DATA_BASE = "https://api.twelvedata.com"
_KC_SYMBOL = "KC1!"  # Coffee C front-month futures


def fetch_twelve_data_coffee(
    api_key: str,
    timeout_s: float = 10.0,
) -> Optional[CoffeeQuote]:
    """Fetch latest Coffee C price from Twelve Data REST API.

    Args:
        api_key: Twelve Data API key.
        timeout_s: HTTP request timeout in seconds.

    Returns:
        CoffeeQuote with price in USD per lb, or None on failure.
    """
    url = f"{_TWELVE_DATA_BASE}/price"
    params = {"symbol": _KC_SYMBOL, "apikey": api_key}

    try:
        r = httpx.get(url, params=params, timeout=timeout_s)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log.warning(
            "twelve_data_fetch_failed",
            symbol=_KC_SYMBOL,
            error=str(e),
            exc_info=True,
        )
        return None

    try:
        price_str = data.get("price")
        if price_str is None:
            # Twelve Data returns {"code": 400, "message": "..."} on errors
            log.warning(
                "twelve_data_no_price",
                symbol=_KC_SYMBOL,
                response=data,
            )
            return None

        price = float(price_str)

        return CoffeeQuote(
            price_usd_per_lb=price,
            observed_at=datetime.now(timezone.utc),
            source_name="Twelve Data (ICE KC1!)",
            source_url=url,
            raw_data=json.dumps(data),
            metadata={
                "symbol": _KC_SYMBOL,
                "provider": "twelve_data",
                "currency": "USD",
                "exchange": "ICE",
            },
        )
    except Exception as e:
        log.warning(
            "twelve_data_parse_failed",
            symbol=_KC_SYMBOL,
            error=str(e),
            exc_info=True,
        )
        return None


def fetch_realtime_coffee_price(
    api_key: Optional[str] = None,
    timeout_s: float = 10.0,
) -> Optional[CoffeeQuote]:
    """Fetch the most up-to-date coffee price using the realtime chain.

    Order:
    1. Twelve Data (when *api_key* is provided)
    2. Yahoo Finance KC=F

    Args:
        api_key: Twelve Data API key.  Pass ``None`` to skip to Yahoo Finance.
        timeout_s: HTTP request timeout per source.

    Returns:
        CoffeeQuote or None if all sources fail.
    """
    if api_key:
        log.info("realtime_price_fetch_start", source="twelve_data")
        quote = fetch_twelve_data_coffee(api_key, timeout_s)
        if quote:
            log.info(
                "realtime_price_fetch_success",
                source="twelve_data",
                price=quote.price_usd_per_lb,
            )
            return quote
        log.warning("realtime_price_twelve_data_failed", fallback="yahoo_finance")

    # Fallback to Yahoo Finance (no API key required)
    from app.providers.coffee_prices import fetch_yahoo_finance_coffee

    log.info("realtime_price_fetch_start", source="yahoo_finance")
    quote = fetch_yahoo_finance_coffee(timeout_s)
    if quote:
        log.info(
            "realtime_price_fetch_success",
            source="yahoo_finance",
            price=quote.price_usd_per_lb,
        )
        return quote

    log.error("realtime_price_all_sources_failed")
    return None
