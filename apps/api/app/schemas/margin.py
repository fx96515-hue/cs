from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from datetime import datetime


class MarginCalcRequest(BaseModel):
    # Core inputs (per kg)
    purchase_price_per_kg: float = Field(..., ge=0, le=10000)
    purchase_currency: str = Field(default="USD", max_length=10)

    # Additive landed costs per kg (freight, insurance, handling, import etc.)
    landed_costs_per_kg: float = Field(default=0.0, ge=0, le=10000)

    # Roasting / processing costs per kg roasted coffee
    roast_and_pack_costs_per_kg: float = Field(default=0.0, ge=0, le=10000)

    # Yield (e.g., green -> roasted). 0.84 means 16% loss.
    yield_factor: float = Field(default=0.84, gt=0, le=1)

    # Selling price per kg roasted coffee
    selling_price_per_kg: float = Field(default=0.0, ge=0, le=10000)
    selling_currency: str = Field(default="EUR", max_length=10)

    # Optional: FX rate used (USD->EUR) if needed by client; calculation here is currency-agnostic unless you provide fx
    fx_usd_to_eur: Optional[float] = Field(None, gt=0, le=100)

    def __init__(self, *args: Any, fx_usd_to_eur: Optional[float] = None, **data: Any) -> None:
        """Provide an explicit __init__ so static type checkers see
        `fx_usd_to_eur` as an optional keyword-only argument.
        """
        if fx_usd_to_eur is not None:
            data["fx_usd_to_eur"] = fx_usd_to_eur
        super().__init__(*args, **data)

    @field_validator("purchase_currency", "selling_currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency codes."""
        valid_currencies = ["USD", "EUR", "PEN", "GBP"]
        v_upper = v.upper().strip()
        if v_upper not in valid_currencies:
            raise ValueError(f"Currency must be one of {valid_currencies}")
        return v_upper


class MarginCalcResult(BaseModel):
    computed_at: datetime
    inputs: dict
    outputs: dict


class MarginRunOut(BaseModel):
    id: int
    lot_id: int
    profile: str
    computed_at: datetime
    inputs: dict
    outputs: dict

    class Config:
        from_attributes = True
