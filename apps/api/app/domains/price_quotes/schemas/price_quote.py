from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


VALID_CURRENCIES = ["USD", "EUR", "PEN", "GBP"]


class PriceQuoteCreate(BaseModel):
    lot_id: Optional[int] = Field(None, gt=0)
    deal_id: Optional[int] = Field(None, gt=0)
    source_id: Optional[int] = Field(None, gt=0)
    price_per_kg: float = Field(..., ge=0)
    currency: str = Field("USD", max_length=8)
    observed_at: datetime
    confidence: Optional[float] = Field(None, ge=0, le=1)
    notes: Optional[str] = Field(None, max_length=500)
    meta: Optional[dict] = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v_upper = v.upper().strip()
        if v_upper not in VALID_CURRENCIES:
            raise ValueError(f"Currency must be one of {VALID_CURRENCIES}")
        return v_upper


class PriceQuoteUpdate(BaseModel):
    lot_id: Optional[int] = Field(None, gt=0)
    deal_id: Optional[int] = Field(None, gt=0)
    source_id: Optional[int] = Field(None, gt=0)
    price_per_kg: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=8)
    observed_at: Optional[datetime] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)
    notes: Optional[str] = Field(None, max_length=500)
    meta: Optional[dict] = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_upper = v.upper().strip()
        if v_upper not in VALID_CURRENCIES:
            raise ValueError(f"Currency must be one of {VALID_CURRENCIES}")
        return v_upper


class PriceQuoteOut(BaseModel):
    id: int
    lot_id: Optional[int] = None
    deal_id: Optional[int] = None
    source_id: Optional[int] = None
    price_per_kg: float
    currency: str
    observed_at: datetime
    confidence: Optional[float] = None
    notes: Optional[str] = None
    meta: Optional[dict] = None

    class Config:
        from_attributes = True
