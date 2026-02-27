"""Multi-source FX rate provider with fallback chain and caching.

Provides resilient FX rate fetching with automatic failover:
1. ECB (European Central Bank)
2. ExchangeRate-API
3. Frankfurter API
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import httpx
import structlog

from app.providers.ecb_fx import fetch_ecb_fx

log = structlog.get_logger()


@dataclass(frozen=True)
class FxRate:
    """Standardized FX rate quote."""

    base: str
    quote: str
    rate: float
    observed_at: datetime
    source_name: str
    source_url: str
    raw_data: str
    metadata: dict


def fetch_exchangerate_api_fx(
    base: str, quote: str, timeout_s: float = 20.0
) -> Optional[FxRate]:
    """Fetch FX rate from ExchangeRate-API (free tier).

    API docs: https://www.exchangerate-api.com/docs/free

    Args:
        base: Base currency code (e.g., "USD")
        quote: Quote currency code (e.g., "EUR")
        timeout_s: Request timeout

    Returns:
        FxRate or None on failure
    """
    base = base.upper().strip()
    quote = quote.upper().strip()

    if base == quote:
        return None

    url = f"https://open.exchangerate-api.com/v6/latest/{base}"

    try:
        r = httpx.get(
            url,
            timeout=timeout_s,
            headers={"User-Agent": "CoffeeStudio/1.0"},
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log.warning(
            "exchangerate_api_fetch_failed",
            base=base,
            quote=quote,
            error=str(e),
            exc_info=True,
        )
        return None

    try:
        rates = data.get("rates", {})
        rate_value = rates.get(quote)

        if rate_value is None:
            log.warning(
                "exchangerate_api_no_rate",
                base=base,
                quote=quote,
                available_rates=list(rates.keys())[:10],
            )
            return None

        # Parse timestamp
        time_updated = data.get("time_last_update_unix")
        if time_updated:
            observed_at = datetime.fromtimestamp(time_updated, tz=timezone.utc)
        else:
            observed_at = datetime.now(timezone.utc)

        return FxRate(
            base=base,
            quote=quote,
            rate=float(rate_value),
            observed_at=observed_at,
            source_name="ExchangeRate-API",
            source_url=url,
            raw_data=json.dumps(data),
            metadata={
                "provider": data.get("provider", "exchangerate-api"),
                "base_code": data.get("base_code", base),
            },
        )
    except Exception as e:
        log.warning(
            "exchangerate_api_parse_failed",
            base=base,
            quote=quote,
            error=str(e),
            exc_info=True,
        )
        return None


def fetch_frankfurter_fx(
    base: str, quote: str, timeout_s: float = 20.0
) -> Optional[FxRate]:
    """Fetch FX rate from Frankfurter API.

    Frankfurter is a free, open-source API for current and historical FX rates.
    API docs: https://www.frankfurter.app/docs/

    Args:
        base: Base currency code (e.g., "USD")
        quote: Quote currency code (e.g., "EUR")
        timeout_s: Request timeout

    Returns:
        FxRate or None on failure
    """
    base = base.upper().strip()
    quote = quote.upper().strip()

    if base == quote:
        return None

    url = "https://api.frankfurter.app/latest"

    try:
        r = httpx.get(
            url,
            timeout=timeout_s,
            headers={"User-Agent": "CoffeeStudio/1.0"},
            params={"from": base, "to": quote},
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log.warning(
            "frankfurter_fetch_failed",
            base=base,
            quote=quote,
            error=str(e),
            exc_info=True,
        )
        return None

    try:
        rates = data.get("rates", {})
        rate_value = rates.get(quote)

        if rate_value is None:
            log.warning(
                "frankfurter_no_rate",
                base=base,
                quote=quote,
                available_rates=list(rates.keys()),
            )
            return None

        # Parse date
        date_str = data.get("date")
        if date_str:
            try:
                observed_at = datetime.fromisoformat(date_str).replace(
                    tzinfo=timezone.utc
                )
            except Exception:
                observed_at = datetime.now(timezone.utc)
        else:
            observed_at = datetime.now(timezone.utc)

        return FxRate(
            base=base,
            quote=quote,
            rate=float(rate_value),
            observed_at=observed_at,
            source_name="Frankfurter",
            source_url=url,
            raw_data=json.dumps(data),
            metadata={
                "amount": data.get("amount", 1.0),
                "base_code": data.get("base", base),
            },
        )
    except Exception as e:
        log.warning(
            "frankfurter_parse_failed",
            base=base,
            quote=quote,
            error=str(e),
            exc_info=True,
        )
        return None


def fetch_ecb_fx_wrapped(
    base: str, quote: str, timeout_s: float = 20.0
) -> Optional[FxRate]:
    """Fetch FX rate from ECB using existing provider.

    Wraps the existing ECB provider to return FxRate format.
    """
    fx = fetch_ecb_fx(base, quote, timeout_s=timeout_s)
    if not fx:
        log.warning("ecb_fetch_failed", base=base, quote=quote)
        return None

    return FxRate(
        base=fx.base,
        quote=fx.quote,
        rate=fx.rate,
        observed_at=fx.observed_at,
        source_name="ECB",
        source_url=fx.source_url,
        raw_data=fx.raw_text,
        metadata={"provider": "ecb"},
    )


def fetch_fx_rate(base: str, quote: str, timeout_s: float = 20.0) -> Optional[FxRate]:
    """Fetch FX rate with automatic fallback chain.

    Tries sources in order:
    1. ECB (European Central Bank)
    2. ExchangeRate-API
    3. Frankfurter API

    Args:
        base: Base currency code (e.g., "USD")
        quote: Quote currency code (e.g., "EUR")
        timeout_s: Timeout for each HTTP request

    Returns:
        FxRate from first successful source, or None if all fail
    """
    base = base.upper().strip()
    quote = quote.upper().strip()

    if base == quote:
        log.warning("fx_rate_same_currency", base=base, quote=quote)
        return None

    # Try ECB first
    log.info("fx_rate_fetch_start", source="ecb", base=base, quote=quote)
    rate = fetch_ecb_fx_wrapped(base, quote, timeout_s)
    if rate:
        log.info(
            "fx_rate_fetch_success",
            source="ecb",
            base=base,
            quote=quote,
            rate=rate.rate,
        )
        return rate

    # Fallback to ExchangeRate-API
    log.info(
        "fx_rate_fetch_fallback", source="exchangerate_api", base=base, quote=quote
    )
    rate = fetch_exchangerate_api_fx(base, quote, timeout_s)
    if rate:
        log.info(
            "fx_rate_fetch_success",
            source="exchangerate_api",
            base=base,
            quote=quote,
            rate=rate.rate,
        )
        return rate

    # Fallback to Frankfurter
    log.info("fx_rate_fetch_fallback", source="frankfurter", base=base, quote=quote)
    rate = fetch_frankfurter_fx(base, quote, timeout_s)
    if rate:
        log.info(
            "fx_rate_fetch_success",
            source="frankfurter",
            base=base,
            quote=quote,
            rate=rate.rate,
        )
        return rate

    log.error("fx_rate_all_sources_failed", base=base, quote=quote)
    return None
