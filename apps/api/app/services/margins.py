from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Tuple

from app.schemas.margin import MarginCalcRequest


def calc_margin(req: MarginCalcRequest) -> Tuple[Dict, Dict]:
    """Currency-agnostic margin calculation.

    Assumptions:
    - purchase_price_per_kg + landed_costs_per_kg are per kg green.
    - yield_factor converts green kg to roasted kg (e.g., 0.84 => 1kg green -> 0.84kg roasted).
    - roast_and_pack_costs_per_kg are per kg roasted.
    """

    # per kg green
    green_total_cost = float(req.purchase_price_per_kg) + float(req.landed_costs_per_kg)

    # convert to per kg roasted
    if req.yield_factor <= 0 or req.yield_factor > 1.0:
        raise ValueError("yield_factor must be within (0,1]")

    cost_per_kg_roasted_from_green = green_total_cost / float(req.yield_factor)
    total_cost_per_kg_roasted = cost_per_kg_roasted_from_green + float(
        req.roast_and_pack_costs_per_kg
    )

    selling = float(req.selling_price_per_kg)

    gross_margin_per_kg = selling - total_cost_per_kg_roasted
    gross_margin_pct = (gross_margin_per_kg / selling) * 100.0 if selling > 0 else None

    inputs = req.model_dump()

    outputs: Dict = {
        "green_total_cost_per_kg": green_total_cost,
        "cost_per_kg_roasted_from_green": cost_per_kg_roasted_from_green,
        "total_cost_per_kg_roasted": total_cost_per_kg_roasted,
        "gross_margin_per_kg": gross_margin_per_kg,
        "gross_margin_pct": gross_margin_pct,
    }

    # Optional EUR view if fx is provided and currencies match expected direction.
    if (
        req.fx_usd_to_eur
        and req.purchase_currency.upper() == "USD"
        and req.selling_currency.upper() == "EUR"
    ):
        fx = float(req.fx_usd_to_eur)
        outputs.update(
            {
                "green_total_cost_per_kg_eur": green_total_cost * fx,
                "total_cost_per_kg_roasted_eur": total_cost_per_kg_roasted * fx,
            }
        )

    outputs["computed_at"] = datetime.now(timezone.utc).isoformat()
    return inputs, outputs
