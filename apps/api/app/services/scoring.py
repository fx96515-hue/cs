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


def compute_cooperative_score(db: Session, coop: Cooperative) -> ScoreBreakdown:
    """Compute score using available hard fields + optional meta hints.

    Notes:
    - All scores are 0..100.
    - Confidence is 0..1 and reflects completeness of hard data.
    """

    reasons: list[str] = []

    # --- Quality ---
    q = None
    meta = coop.meta or {}
    if coop.quality_score is not None:
        q = _clamp(float(coop.quality_score))
        reasons.append("Qualität: quality_score Feld gesetzt")
    elif isinstance(meta.get("sca_score"), (int, float)):
        q = _map_sca_to_score(float(meta["sca_score"]))
        reasons.append("Qualität: SCA Score aus meta.sca_score")

    # --- Reliability ---
    r = None
    if coop.reliability_score is not None:
        r = _clamp(float(coop.reliability_score))
        reasons.append("Zuverlässigkeit: reliability_score Feld gesetzt")
    elif isinstance(meta.get("reliability"), (int, float)):
        r = _clamp(float(meta["reliability"]))
        reasons.append("Zuverlässigkeit: meta.reliability")

    # --- Economics ---
    e = None
    if coop.economics_score is not None:
        e = _clamp(float(coop.economics_score))
        reasons.append("Wirtschaftlichkeit: economics_score Feld gesetzt")
    else:
        fob = meta.get("fob_usd_per_kg")
        if isinstance(fob, (int, float)):
            # Use coffee 'C' as a crude proxy: COFFEE_C:USD_LB => convert to USD/kg (1 lb=0.453592)
            obs = _get_latest_observation(db, "COFFEE_C:USD_LB")
            if obs and obs.value > 0:
                ref_usd_per_kg = float(obs.value) / 0.453592
                # cheaper than reference improves score; more expensive reduces.
                # ratio 0.7 => +25; ratio 1.3 => -25
                ratio = float(fob) / ref_usd_per_kg
                e = _clamp(50.0 + (1.0 - ratio) * 83.0)
                reasons.append(
                    f"Wirtschaftlichkeit: FOB vs Referenz (FOB {fob:.2f} USD/kg; Ref ~{ref_usd_per_kg:.2f} USD/kg)"
                )
            else:
                # without reference, we stay conservative-neutral
                e = 50.0
                reasons.append(
                    "Wirtschaftlichkeit: FOB vorhanden, aber keine COFFEE_C Referenz -> neutral"
                )

    # --- Confidence ---
    # Hard signals:
    #  - quality, reliability, economics
    #  - contact channel (email or website)
    #  - region/altitude metadata
    signals = 0
    possible = 5
    if q is not None:
        signals += 1
    if r is not None:
        signals += 1
    if e is not None:
        signals += 1
    if coop.contact_email or coop.website:
        signals += 1
    if coop.region or coop.altitude_m is not None:
        signals += 1

    confidence = max(0.0, min(1.0, signals / possible))

    # --- Total ---
    total = None
    if q is not None and r is not None and e is not None:
        total = _clamp(
            q * DEFAULT_WEIGHTS["quality"]
            + r * DEFAULT_WEIGHTS["reliability"]
            + e * DEFAULT_WEIGHTS["economics"]
        )
    else:
        # If incomplete: compute using available dimensions but down-weight via confidence
        dims: list[Tuple[str, Optional[float]]] = [
            ("quality", q),
            ("reliability", r),
            ("economics", e),
        ]
        present = [(k, v) for (k, v) in dims if v is not None]
        if present:
            w_sum = sum(DEFAULT_WEIGHTS[k] for k, _ in present)
            base = sum(v * DEFAULT_WEIGHTS[k] for k, v in present) / w_sum
            total = _clamp(base * (0.5 + 0.5 * confidence))

    return ScoreBreakdown(
        quality=q,
        reliability=r,
        economics=e,
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
