"""Multi-source coffee price provider with fallback chain.

Provides resilient coffee price fetching with automatic failover:
1. Yahoo Finance (KC=F ICE Coffee C Futures)
2. Stooq (existing provider)
3. ICO static benchmark (last resort)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import httpx
import structlog

from app.providers.stooq import fetch_stooq_last_close

log = structlog.get_logger()


@dataclass(frozen=True)
class CoffeeQuote:
    """Standardized coffee price quote."""

    price_usd_per_lb: float
    observed_at: datetime
    source_name: str
    source_url: str
    raw_data: str
    metadata: dict


def fetch_yahoo_finance_coffee(timeout_s: float = 20.0) -> Optional[CoffeeQuote]:
    """Fetch KC=F (Coffee C Futures) from Yahoo Finance API.

    Yahoo Finance provides free access to commodity futures data.
    KC=F is the ICE Coffee C Arabica futures contract.

    Returns:
        CoffeeQuote with price in USD per lb, or None on failure
    """
    symbol = "KC=F"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

    try:
        r = httpx.get(
            url,
            timeout=timeout_s,
            headers={"User-Agent": "CoffeeStudio/1.0"},
            params={"interval": "1d", "range": "1d"},
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log.warning(
            "yahoo_finance_fetch_failed",
            symbol=symbol,
            error=str(e),
            exc_info=True,
        )
        return None

    try:
        result = data.get("chart", {}).get("result", [])
        if not result:
            log.warning("yahoo_finance_no_results", symbol=symbol)
            return None

        quote_data = result[0]
        meta = quote_data.get("meta", {})
        regular_price = meta.get("regularMarketPrice")

        if regular_price is None:
            log.warning("yahoo_finance_no_price", symbol=symbol, meta=meta)
            return None

        # Yahoo timestamps are in seconds since epoch
        timestamp = meta.get("regularMarketTime")
        if timestamp:
            observed_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        else:
            observed_at = datetime.now(timezone.utc)

        return CoffeeQuote(
            price_usd_per_lb=float(regular_price),
            observed_at=observed_at,
            source_name="Yahoo Finance",
            source_url=url,
            raw_data=json.dumps(data),
            metadata={
                "symbol": symbol,
                "currency": meta.get("currency", "USD"),
                "exchange": meta.get("exchangeName", "ICE"),
            },
        )
    except Exception as e:
        log.warning(
            "yahoo_finance_parse_failed",
            symbol=symbol,
            error=str(e),
            exc_info=True,
        )
        return None


def fetch_stooq_coffee(timeout_s: float = 20.0) -> Optional[CoffeeQuote]:
    """Fetch coffee price from Stooq using existing provider.

    Wraps the existing Stooq provider to return CoffeeQuote format.
    """
    quote = fetch_stooq_last_close("kc.f", timeout_s=timeout_s)
    if not quote:
        log.warning("stooq_fetch_failed", symbol="kc.f")
        return None

    return CoffeeQuote(
        price_usd_per_lb=quote.close,
        observed_at=quote.observed_at,
        source_name="Stooq",
        source_url=quote.source_url,
        raw_data=quote.raw_text,
        metadata={"symbol": quote.symbol},
    )


def fetch_ico_fallback() -> CoffeeQuote:
    """Return static ICO benchmark as last-resort fallback.

    This provides a reasonable fallback when all live sources fail.
    Based on historical ICO composite indicator averages.
    """
    return CoffeeQuote(
        price_usd_per_lb=2.10,
        observed_at=datetime.now(timezone.utc),
        source_name="ICO Static Fallback",
        source_url="https://www.ico.org/",
        raw_data=json.dumps(
            {
                "note": "Static fallback price based on ICO historical averages",
                "arabica_mild_average": 2.10,
            }
        ),
        metadata={"fallback": True, "type": "arabica_mild"},
    )


def fetch_coffee_price(
    use_fallback: bool = True, timeout_s: float = 20.0
) -> Optional[CoffeeQuote]:
    """Fetch coffee price with automatic fallback chain.

    Tries sources in order:
    1. Yahoo Finance (KC=F)
    2. Stooq (KC.F)
    3. ICO static benchmark (if use_fallback=True)

    Args:
        use_fallback: If True, return static ICO fallback if all sources fail
        timeout_s: Timeout for each HTTP request

    Returns:
        CoffeeQuote from first successful source, or None if all fail
    """
    # Try Yahoo Finance first
    log.info("coffee_price_fetch_start", source="yahoo_finance")
    quote = fetch_yahoo_finance_coffee(timeout_s)
    if quote:
        log.info(
            "coffee_price_fetch_success",
            source="yahoo_finance",
            price=quote.price_usd_per_lb,
        )
        return quote

    # Fallback to Stooq
    log.info("coffee_price_fetch_fallback", source="stooq")
    quote = fetch_stooq_coffee(timeout_s)
    if quote:
        log.info(
            "coffee_price_fetch_success",
            source="stooq",
            price=quote.price_usd_per_lb,
        )
        return quote

    # Last resort: static ICO benchmark
    if use_fallback:
        log.warning("coffee_price_all_sources_failed", using_fallback=True)
        return fetch_ico_fallback()

    log.error("coffee_price_all_sources_failed", using_fallback=False)
    return None
