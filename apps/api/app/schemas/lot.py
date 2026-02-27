from pydantic import BaseModel, Field, field_validator
from typing import Optional


class LotCreate(BaseModel):
    cooperative_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=2, max_length=255)
    crop_year: Optional[int] = Field(None, ge=2000, le=2100)
    incoterm: Optional[str] = Field(None, max_length=50)
    price_per_kg: Optional[float] = Field(None, ge=0, le=10000)
    currency: Optional[str] = Field(None, max_length=10)
    weight_kg: Optional[float] = Field(None, gt=0, le=100000)
    expected_cupping_score: Optional[float] = Field(None, ge=0, le=100)
    varieties: Optional[str] = Field(None, max_length=500)
    processing: Optional[str] = Field(None, max_length=255)
    availability_window: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    meta: Optional[dict] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate lot name for XSS prevention."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        # Prevent XSS attempts
        if any(
            pattern in v.lower() for pattern in ["<script", "<iframe", "javascript:"]
        ):
            raise ValueError("Invalid characters in name")
        return v.strip()

    @field_validator("incoterm")
    @classmethod
    def validate_incoterm(cls, v: Optional[str]) -> Optional[str]:
        """Validate incoterm values."""
        if v is None:
            return v
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

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        """Validate currency codes."""
        if v is None:
            return v
        valid_currencies = ["USD", "EUR", "PEN", "GBP"]
        v_upper = v.upper().strip()
        if v_upper not in valid_currencies:
            raise ValueError(f"Currency must be one of {valid_currencies}")
        return v_upper


class LotUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    crop_year: Optional[int] = Field(None, ge=2000, le=2100)
    incoterm: Optional[str] = Field(None, max_length=50)
    price_per_kg: Optional[float] = Field(None, ge=0, le=10000)
    currency: Optional[str] = Field(None, max_length=10)
    weight_kg: Optional[float] = Field(None, gt=0, le=100000)
    expected_cupping_score: Optional[float] = Field(None, ge=0, le=100)
    varieties: Optional[str] = Field(None, max_length=500)
    processing: Optional[str] = Field(None, max_length=255)
    availability_window: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    meta: Optional[dict] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate lot name for XSS prevention."""
        if v is None:
            return v
        if not v.strip():
            raise ValueError("Name cannot be empty")
        # Prevent XSS attempts
        if any(
            pattern in v.lower() for pattern in ["<script", "<iframe", "javascript:"]
        ):
            raise ValueError("Invalid characters in name")
        return v.strip()

    @field_validator("incoterm")
    @classmethod
    def validate_incoterm(cls, v: Optional[str]) -> Optional[str]:
        """Validate incoterm values."""
        if v is None:
            return v
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

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        """Validate currency codes."""
        if v is None:
            return v
        valid_currencies = ["USD", "EUR", "PEN", "GBP"]
        v_upper = v.upper().strip()
        if v_upper not in valid_currencies:
            raise ValueError(f"Currency must be one of {valid_currencies}")
        return v_upper


class LotOut(BaseModel):
    id: int
    cooperative_id: int
    name: str
    crop_year: Optional[int] = None
    incoterm: Optional[str] = None
    price_per_kg: Optional[float] = None
    currency: Optional[str] = None
    weight_kg: Optional[float] = None
    expected_cupping_score: Optional[float] = None
    varieties: Optional[str] = None
    processing: Optional[str] = None
    availability_window: Optional[str] = None
    notes: Optional[str] = None
    meta: Optional[dict] = None

    class Config:
        from_attributes = True
