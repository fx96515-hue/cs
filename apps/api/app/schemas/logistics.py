from pydantic import BaseModel, Field, field_validator


class LandedCostRequest(BaseModel):
    weight_kg: float = Field(..., gt=0, le=50000)
    green_price_usd_per_kg: float = Field(..., ge=0, le=100)
    incoterm: str = Field(default="FOB", max_length=10)
    freight_usd: float = Field(default=0.0, ge=0, le=1000000)
    insurance_pct: float = Field(default=0.006, ge=0, le=1)
    handling_eur: float = Field(default=0.0, ge=0, le=100000)
    inland_trucking_eur: float = Field(default=0.0, ge=0, le=100000)
    duty_pct: float = Field(default=0.0, ge=0, le=1)
    vat_pct: float = Field(default=0.19, ge=0, le=1)

    @field_validator("incoterm")
    @classmethod
    def validate_incoterm(cls, v: str) -> str:
        """Validate incoterm values."""
        valid_incoterms = [
            "EXW",
            "FOB",
            "CIF",
            "CFR",
            "DAP",
            "DDP",
            "FCA",
            "CPT",
            "CIP",
        ]
        v_upper = v.upper().strip()
        if v_upper not in valid_incoterms:
            raise ValueError(f"Incoterm must be one of {valid_incoterms}")
        return v_upper


class LandedCostResponse(BaseModel):
    status: str
    inputs: dict
    fx: dict
    breakdown_eur: dict
