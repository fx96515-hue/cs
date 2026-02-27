from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.market import MarketObservation


DEFAULT_USD_EUR = 0.92


def _latest_usd_eur(db: Session) -> tuple[float, str]:
    """Return (usd_eur, source)."""
    obs = (
        db.query(MarketObservation)
        .filter(MarketObservation.key == "FX:USD_EUR")
        .order_by(MarketObservation.observed_at.desc())
        .first()
    )
    if not obs:
        return DEFAULT_USD_EUR, "fallback"
    return float(obs.value), f"obs:{obs.id}"


def calc_landed_cost(
    db: Session,
    *,
    weight_kg: float,
    green_price_usd_per_kg: float,
    incoterm: str = "FOB",
    freight_usd: float = 0.0,
    insurance_pct: float = 0.006,
    handling_eur: float = 0.0,
    inland_trucking_eur: float = 0.0,
    duty_pct: float = 0.0,
    vat_pct: float = 0.19,
) -> dict[str, Any]:
    """Deterministic landed-cost calculator (raw coffee).

    Notes:
    - This is a pragmatic v1 (transparent assumptions) used as a baseline.
    - duty_pct defaults to 0.0 because many green coffee imports are duty-free,
      but you can override per HS-code/country.
    """
    if weight_kg <= 0:
        raise ValueError("weight_kg must be > 0")
    if green_price_usd_per_kg < 0:
        raise ValueError("green_price_usd_per_kg must be >= 0")

    incoterm = (incoterm or "FOB").upper().strip()

    usd_eur, fx_src = _latest_usd_eur(db)
    goods_usd = weight_kg * green_price_usd_per_kg
    goods_eur = goods_usd * usd_eur

    freight_eur = max(0.0, freight_usd) * usd_eur
    insurance_eur = (goods_eur + freight_eur) * max(0.0, insurance_pct)

    # CIF base (for duty/vat calc when applicable)
    cif_eur = goods_eur + freight_eur + insurance_eur

    duty_eur = cif_eur * max(0.0, duty_pct)
    vat_base_eur = (
        cif_eur + duty_eur + max(0.0, handling_eur) + max(0.0, inland_trucking_eur)
    )
    vat_eur = vat_base_eur * max(0.0, vat_pct)

    total_eur = vat_base_eur + vat_eur
    landed_eur_per_kg = total_eur / weight_kg

    return {
        "status": "ok",
        "calculated_at": datetime.now(timezone.utc),
        "inputs": {
            "weight_kg": weight_kg,
            "green_price_usd_per_kg": green_price_usd_per_kg,
            "incoterm": incoterm,
            "freight_usd": freight_usd,
            "insurance_pct": insurance_pct,
            "handling_eur": handling_eur,
            "inland_trucking_eur": inland_trucking_eur,
            "duty_pct": duty_pct,
            "vat_pct": vat_pct,
        },
        "fx": {"usd_eur": usd_eur, "source": fx_src},
        "breakdown_eur": {
            "goods": goods_eur,
            "freight": freight_eur,
            "insurance": insurance_eur,
            "cif": cif_eur,
            "duty": duty_eur,
            "handling": max(0.0, handling_eur),
            "inland_trucking": max(0.0, inland_trucking_eur),
            "vat_base": vat_base_eur,
            "vat": vat_eur,
            "total": total_eur,
            "landed_eur_per_kg": landed_eur_per_kg,
        },
    }
