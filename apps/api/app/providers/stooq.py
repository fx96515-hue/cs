from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from typing import Optional

import httpx


@dataclass(frozen=True)
class OhlcQuote:
    symbol: str
    close: float
    observed_at: datetime
    source_url: str
    raw_text: str


def _stooq_csv_url(symbol: str, interval: str = "d") -> str:
    # Stooq supports CSV downloads via /q/d/l/ (used widely by tools).
    # Example: https://stooq.com/q/d/l/?s=kc.f&i=d
    sym = symbol.strip().lower()
    return f"https://stooq.com/q/d/l/?s={sym}&i={interval}"


def fetch_stooq_last_close(symbol: str, timeout_s: float = 20.0) -> Optional[OhlcQuote]:
    """Fetch last available close price for a symbol from Stooq (CSV).

    Note: Stooq coverage for some commodities can be flaky; this returns None
    if the endpoint returns no rows.
    """
    url = _stooq_csv_url(symbol, "d")
    try:
        r = httpx.get(
            url, timeout=timeout_s, headers={"User-Agent": "CoffeeStudio/1.0"}
        )
        r.raise_for_status()
        text = r.text
    except Exception:
        return None

    # CSV header: Date,Open,High,Low,Close,Volume
    try:
        rows = list(csv.DictReader(StringIO(text)))
    except Exception:
        return None
    if not rows:
        return None

    last = rows[-1]
    dt_str = (last.get("Date") or "").strip()
    close_str = (last.get("Close") or "").strip()
    if not dt_str or not close_str:
        return None

    try:
        close = float(close_str)
    except Exception:
        return None

    # Stooq dates are usually YYYY-MM-DD.
    try:
        observed_at = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
    except Exception:
        observed_at = datetime.now(timezone.utc)

    return OhlcQuote(
        symbol=symbol,
        close=close,
        observed_at=observed_at,
        source_url=url,
        raw_text=text,
    )
