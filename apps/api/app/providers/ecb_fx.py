from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from xml.etree import ElementTree as ET

import httpx


# ECB publishes a daily XML with reference rates where EUR is the base currency.
ECB_DAILY_XML = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"


@dataclass(frozen=True)
class FxQuote:
    base: str
    quote: str
    rate: float
    observed_at: datetime
    source_url: str
    raw_text: str


def _normalize_currency(value: str) -> str:
    return value.upper().strip()


def _fetch_xml(timeout_s: float) -> Optional[str]:
    try:
        response = httpx.get(ECB_DAILY_XML, timeout=timeout_s)
        response.raise_for_status()
        return response.text
    except Exception:
        return None


def _parse_xml(xml_text: str) -> Optional[ET.Element]:
    try:
        return ET.fromstring(xml_text)
    except Exception:
        return None


def _find_time_cube(root: ET.Element) -> Optional[ET.Element]:
    for node in root.iter():
        if node.tag.endswith("Cube") and "time" in node.attrib:
            return node
    return None


def _parse_observed_at(time_value: Optional[str]) -> datetime:
    if not time_value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(time_value).replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def _extract_rates(time_node: ET.Element) -> dict[str, float]:
    rates: dict[str, float] = {}
    for node in time_node:
        if not node.tag.endswith("Cube"):
            continue
        currency = node.attrib.get("currency")
        rate_value = node.attrib.get("rate")
        if not currency or not rate_value:
            continue
        try:
            rates[currency.upper()] = float(rate_value)
        except Exception:
            continue
    return rates


def _eur_to_rate(currency: str, rates: dict[str, float]) -> Optional[float]:
    if currency == "EUR":
        return 1.0
    return rates.get(currency)


def fetch_ecb_fx(base: str, quote: str, timeout_s: float = 20.0) -> Optional[FxQuote]:
    """Fetch FX reference rate from ECB daily XML.

    ECB provides rates with base EUR (1 EUR = X QUOTE). If you ask for
    USD->EUR we invert the EUR->USD rate.
    """
    base = _normalize_currency(base)
    quote = _normalize_currency(quote)
    if base == quote:
        return None

    xml_text = _fetch_xml(timeout_s)
    if xml_text is None:
        return None

    root = _parse_xml(xml_text)
    if root is None:
        return None

    time_node = _find_time_cube(root)
    if time_node is None:
        return None

    observed_at = _parse_observed_at(time_node.attrib.get("time"))
    rates = _extract_rates(time_node)

    eur_to_base = _eur_to_rate(base, rates)
    eur_to_quote = _eur_to_rate(quote, rates)
    if eur_to_base is None or eur_to_quote is None:
        return None

    rate_value = eur_to_quote / eur_to_base

    return FxQuote(
        base=base,
        quote=quote,
        rate=rate_value,
        observed_at=observed_at,
        source_url=ECB_DAILY_XML,
        raw_text=xml_text,
    )
