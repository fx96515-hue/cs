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


def fetch_ecb_fx(base: str, quote: str, timeout_s: float = 20.0) -> Optional[FxQuote]:
    """Fetch FX reference rate from ECB daily XML.

    ECB provides rates with base EUR (1 EUR = X QUOTE). If you ask for
    USD->EUR we invert the EUR->USD rate.
    """
    base = base.upper().strip()
    quote = quote.upper().strip()
    if base == quote:
        return None

    try:
        r = httpx.get(ECB_DAILY_XML, timeout=timeout_s)
        r.raise_for_status()
        xml_text = r.text
    except Exception:
        return None

    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return None

    # XML uses namespaces; simplest is to search by suffix.
    time_node = None
    for n in root.iter():
        if n.tag.endswith("Cube") and "time" in n.attrib:
            time_node = n
            break
    if time_node is None:
        return None

    dt_str = time_node.attrib.get("time")
    if not dt_str:
        observed_at = datetime.now(timezone.utc)
    else:
        try:
            observed_at = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
        except Exception:
            observed_at = datetime.now(timezone.utc)

    # collect rates: quote_ccy -> rate (EUR base)
    rates: dict[str, float] = {}
    for n in time_node:
        if not n.tag.endswith("Cube"):
            continue
        ccy = n.attrib.get("currency")
        rate = n.attrib.get("rate")
        if not ccy or not rate:
            continue
        try:
            rates[ccy.upper()] = float(rate)
        except Exception:
            continue

    # ECB does not include EUR as a currency node; it's the implicit base.
    def eur_to(ccy: str) -> Optional[float]:
        if ccy == "EUR":
            return 1.0
        return rates.get(ccy)

    eur_to_base = eur_to(base)
    eur_to_quote = eur_to(quote)
    if eur_to_base is None or eur_to_quote is None:
        return None

    # Convert base->quote via EUR: (EUR->quote) / (EUR->base)
    rate_value: float = eur_to_quote / eur_to_base

    return FxQuote(
        base=base,
        quote=quote,
        rate=rate_value,
        observed_at=observed_at,
        source_url=ECB_DAILY_XML,
        raw_text=xml_text,
    )
