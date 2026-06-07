from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.cooperative import Cooperative
from app.models.market import MarketObservation


@dataclass(frozen=True)
class ScoreBreakdown:
    quality: Optional[float]
    reliability: Optional[float]
    economics: Optional[float]
    total: Optional[float]
    confidence: float
    reasons: list[str]


DEFAULT_WEIGHTS = {
    "quality": 0.45,
    "reliability": 0.30,
    "economics": 0.25,
}


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def _map_sca_to_score(sca: float) -> float:
    # SCA specialty starts at 80. Map 80->60, 90->100, clamp.
    return _clamp(60.0 + (sca - 80.0) * 4.0)


def _get_latest_observation(db: Session, key: str) -> Optional[MarketObservation]:
    return (
        db.query(MarketObservation)
        .filter(MarketObservation.key == key)
        .order_by(MarketObservation.observed_at.desc())
        .first()
    )


def _compute_quality(
    coop: Cooperative, meta: dict, reasons: list[str]
) -> Optional[float]:
    if coop.quality_score is not None:
        reasons.append("Qualitaet: quality_score Feld gesetzt")
        return _clamp(float(coop.quality_score))

    sca_score = meta.get("sca_score")
    if isinstance(sca_score, (int, float)):
        reasons.append("Qualitaet: SCA Score aus meta.sca_score")
        return _map_sca_to_score(float(sca_score))

    return None


def _compute_reliability(
    coop: Cooperative, meta: dict, reasons: list[str]
) -> Optional[float]:
    if coop.reliability_score is not None:
        reasons.append("Zuverlaessigkeit: reliability_score Feld gesetzt")
        return _clamp(float(coop.reliability_score))

    reliability = meta.get("reliability")
    if isinstance(reliability, (int, float)):
        reasons.append("Zuverlaessigkeit: meta.reliability")
        return _clamp(float(reliability))

    return None


def _compute_economics(
    db: Session, coop: Cooperative, meta: dict, reasons: list[str]
) -> Optional[float]:
    if coop.economics_score is not None:
        reasons.append("Wirtschaftlichkeit: economics_score Feld gesetzt")
        return _clamp(float(coop.economics_score))

    fob = meta.get("fob_usd_per_kg")
    if not isinstance(fob, (int, float)):
        return None

    obs = _get_latest_observation(db, "COFFEE_C:USD_LB")
    if obs and obs.value > 0:
        ref_usd_per_kg = float(obs.value) / 0.453592
        ratio = float(fob) / ref_usd_per_kg
        reasons.append(
            f"Wirtschaftlichkeit: FOB vs Referenz (FOB {fob:.2f} USD/kg; Ref ~{ref_usd_per_kg:.2f} USD/kg)"
        )
        return _clamp(50.0 + (1.0 - ratio) * 83.0)

    reasons.append(
        "Wirtschaftlichkeit: FOB vorhanden, aber keine COFFEE_C Referenz -> neutral"
    )
    return 50.0


def _compute_confidence(
    coop: Cooperative,
    quality: Optional[float],
    reliability: Optional[float],
    economics: Optional[float],
) -> float:
    signals = 0
    if quality is not None:
        signals += 1
    if reliability is not None:
        signals += 1
    if economics is not None:
        signals += 1
    if coop.contact_email or coop.website:
        signals += 1
    if coop.region or coop.altitude_m is not None:
        signals += 1
    return max(0.0, min(1.0, signals / 5))


def _compute_total(
    quality: Optional[float],
    reliability: Optional[float],
    economics: Optional[float],
    confidence: float,
) -> Optional[float]:
    if quality is not None and reliability is not None and economics is not None:
        return _clamp(
            quality * DEFAULT_WEIGHTS["quality"]
            + reliability * DEFAULT_WEIGHTS["reliability"]
            + economics * DEFAULT_WEIGHTS["economics"]
        )

    dims: list[Tuple[str, Optional[float]]] = [
        ("quality", quality),
        ("reliability", reliability),
        ("economics", economics),
    ]
    present = [(key, value) for (key, value) in dims if value is not None]
    if not present:
        return None

    weight_sum = sum(DEFAULT_WEIGHTS[key] for key, _ in present)
    base = sum(value * DEFAULT_WEIGHTS[key] for key, value in present) / weight_sum
    return _clamp(base * (0.5 + 0.5 * confidence))


def compute_cooperative_score(db: Session, coop: Cooperative) -> ScoreBreakdown:
    """Compute score using available hard fields + optional meta hints.

    Notes:
    - All scores are 0..100.
    - Confidence is 0..1 and reflects completeness of hard data.
    """

    reasons: list[str] = []
    meta = coop.meta or {}

    quality = _compute_quality(coop, meta, reasons)
    reliability = _compute_reliability(coop, meta, reasons)
    economics = _compute_economics(db, coop, meta, reasons)

    confidence = _compute_confidence(coop, quality, reliability, economics)
    total = _compute_total(quality, reliability, economics, confidence)

    return ScoreBreakdown(
        quality=quality,
        reliability=reliability,
        economics=economics,
        total=total,
        confidence=confidence,
        reasons=reasons,
    )


def recompute_and_persist_cooperative(db: Session, coop: Cooperative) -> ScoreBreakdown:
    breakdown = compute_cooperative_score(db, coop)
    coop.quality_score = breakdown.quality
    coop.reliability_score = breakdown.reliability
    coop.economics_score = breakdown.economics
    coop.total_score = breakdown.total
    coop.confidence = breakdown.confidence
    coop.last_scored_at = datetime.now(timezone.utc)
    db.add(coop)
    db.commit()
    db.refresh(coop)
    return breakdown
