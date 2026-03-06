from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.core.validation import validate_text_field


VALID_CURRENCIES = ["USD", "EUR", "PEN", "GBP"]
VALID_STATUSES = ["open", "in_progress", "closed", "canceled"]


class DealCreate(BaseModel):
    cooperative_id: Optional[int] = Field(None, gt=0)
    roaster_id: Optional[int] = Field(None, gt=0)
    lot_id: Optional[int] = Field(None, gt=0)
    status: str = Field("open")
    incoterm: Optional[str] = Field(None, max_length=16)
    price_per_kg: Optional[float] = Field(None, ge=0, le=10000)
    currency: Optional[str] = Field(None, max_length=8)
    weight_kg: Optional[float] = Field(None, gt=0, le=100000)
    value_total: Optional[float] = Field(None, ge=0)
    value_eur: Optional[float] = Field(None, ge=0)
    origin_country: Optional[str] = Field(None, max_length=64)
    origin_region: Optional[str] = Field(None, max_length=128)
    variety: Optional[str] = Field(None, max_length=128)
    process_method: Optional[str] = Field(None, max_length=128)
    quality_grade: Optional[str] = Field(None, max_length=64)
    cupping_score: Optional[float] = Field(None, ge=0, le=100)
    certifications: Optional[dict] = None
    closed_at: Optional[datetime] = None
    notes: Optional[str] = None
    meta: Optional[dict] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        v_lower = v.strip().lower()
        if v_lower not in VALID_STATUSES:
            raise ValueError(f"Status must be one of {VALID_STATUSES}")
        return v_lower

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_upper = v.upper().strip()
        if v_upper not in VALID_CURRENCIES:
            raise ValueError(f"Currency must be one of {VALID_CURRENCIES}")
        return v_upper

    @field_validator("incoterm")
    @classmethod
    def validate_incoterm(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_text_field(v, field_name="incoterm", max_length=16)


class DealUpdate(BaseModel):
    cooperative_id: Optional[int] = Field(None, gt=0)
    roaster_id: Optional[int] = Field(None, gt=0)
    lot_id: Optional[int] = Field(None, gt=0)
    status: Optional[str] = None
    incoterm: Optional[str] = Field(None, max_length=16)
    price_per_kg: Optional[float] = Field(None, ge=0, le=10000)
    currency: Optional[str] = Field(None, max_length=8)
    weight_kg: Optional[float] = Field(None, gt=0, le=100000)
    value_total: Optional[float] = Field(None, ge=0)
    value_eur: Optional[float] = Field(None, ge=0)
    origin_country: Optional[str] = Field(None, max_length=64)
    origin_region: Optional[str] = Field(None, max_length=128)
    variety: Optional[str] = Field(None, max_length=128)
    process_method: Optional[str] = Field(None, max_length=128)
    quality_grade: Optional[str] = Field(None, max_length=64)
    cupping_score: Optional[float] = Field(None, ge=0, le=100)
    certifications: Optional[dict] = None
    closed_at: Optional[datetime] = None
    notes: Optional[str] = None
    meta: Optional[dict] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_lower = v.strip().lower()
        if v_lower not in VALID_STATUSES:
            raise ValueError(f"Status must be one of {VALID_STATUSES}")
        return v_lower

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_upper = v.upper().strip()
        if v_upper not in VALID_CURRENCIES:
            raise ValueError(f"Currency must be one of {VALID_CURRENCIES}")
        return v_upper

    @field_validator("incoterm")
    @classmethod
    def validate_incoterm(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_text_field(v, field_name="incoterm", max_length=16)


class DealOut(BaseModel):
    id: int
    cooperative_id: Optional[int] = None
    roaster_id: Optional[int] = None
    lot_id: Optional[int] = None
    status: str
    incoterm: Optional[str] = None
    price_per_kg: Optional[float] = None
    currency: Optional[str] = None
    weight_kg: Optional[float] = None
    value_total: Optional[float] = None
    value_eur: Optional[float] = None
    origin_country: Optional[str] = None
    origin_region: Optional[str] = None
    variety: Optional[str] = None
    process_method: Optional[str] = None
    quality_grade: Optional[str] = None
    cupping_score: Optional[float] = None
    certifications: Optional[dict] = None
    closed_at: Optional[datetime] = None
    notes: Optional[str] = None
    meta: Optional[dict] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
