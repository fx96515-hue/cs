from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.market import MarketObservation
from app.models.source import Source


def get_or_create_source(
    db: Session,
    name: str,
    url: Optional[str] = None,
    kind: str = "web",
    reliability: Optional[float] = None,
    notes: Optional[str] = None,
) -> Source:
    src = db.query(Source).filter(Source.name == name).first()
    if src:
        # keep best known URL, etc.
        if url and not src.url:
            src.url = url
        if reliability is not None and src.reliability is None:
            src.reliability = reliability
        if notes and not src.notes:
            src.notes = notes
        db.commit()
        return src

    src = Source(name=name, url=url, kind=kind, reliability=reliability, notes=notes)
    db.add(src)
    db.commit()
    db.refresh(src)
    return src


def upsert_market_observation(
    db: Session,
    *,
    key: str,
    value: float,
    observed_at: datetime,
    unit: Optional[str] = None,
    currency: Optional[str] = None,
    source_name: Optional[str] = None,
    source_url: Optional[str] = None,
    raw_text: Optional[str] = None,
    meta: Optional[dict] = None,
) -> MarketObservation:
    """Idempotent write for market data.

    With the unique constraint (key, observed_at, source_id) this becomes a
    true UPSERT. We still do a read-first approach for portability.
    """
    src_id: Optional[int] = None
    if source_name:
        src = get_or_create_source(db, source_name, url=source_url, kind="web")
        src_id = src.id

    q = db.query(MarketObservation).filter(
        MarketObservation.key == key,
        MarketObservation.observed_at == observed_at,
    )
    if src_id is None:
        q = q.filter(MarketObservation.source_id.is_(None))
    else:
        q = q.filter(MarketObservation.source_id == src_id)

    existing = q.first()
    if existing:
        existing.value = value
        existing.unit = unit
        existing.currency = currency
        if raw_text is not None:
            existing.raw_text = raw_text
        if meta is not None:
            existing.meta = meta
        db.commit()
        db.refresh(existing)
        return existing

    obs = MarketObservation(
        key=key,
        value=value,
        unit=unit,
        currency=currency,
        observed_at=observed_at,
        source_id=src_id,
        raw_text=raw_text,
        meta=meta,
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return obs
