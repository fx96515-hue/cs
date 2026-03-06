from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.core.validation import validate_text_field


class TransportEventCreate(BaseModel):
    shipment_id: int = Field(..., gt=0)
    event_type: str = Field(..., max_length=64)
    location: Optional[str] = Field(None, max_length=200)
    occurred_at: datetime
    status: Optional[str] = Field(None, max_length=64)
    details: Optional[dict] = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        return validate_text_field(v, field_name="event_type", max_length=64)

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: Optional[str]) -> Optional[str]:
        return validate_text_field(v, field_name="location", max_length=200)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        return validate_text_field(v, field_name="status", max_length=64)


class TransportEventOut(BaseModel):
    id: int
    shipment_id: int
    event_type: str
    location: Optional[str] = None
    occurred_at: datetime
    status: Optional[str] = None
    details: Optional[dict] = None

    class Config:
        from_attributes = True
