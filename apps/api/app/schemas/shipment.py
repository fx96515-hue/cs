from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

from app.core.validation import validate_text_field


class TrackingEvent(BaseModel):
    timestamp: str
    location: str
    event: str
    details: Optional[str] = None


class ShipmentCreate(BaseModel):
    lot_id: Optional[int] = None
    cooperative_id: Optional[int] = None
    roaster_id: Optional[int] = None
    container_number: str = Field(..., min_length=5, max_length=50)
    bill_of_lading: str = Field(..., min_length=3, max_length=100)
    weight_kg: float = Field(..., gt=0)
    container_type: str = Field(..., pattern="^(20ft|40ft|40ft_hc)$")
    origin_port: str = Field(..., max_length=100)
    destination_port: str = Field(..., max_length=100)
    departure_date: Optional[str] = None
    estimated_arrival: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("origin_port", "destination_port")
    @classmethod
    def validate_port(cls, v: str) -> str:
        """Validate port names for XSS prevention."""
        if not v or not v.strip():
            raise ValueError("Port name cannot be empty")
        result = validate_text_field(
            v,
            field_name="port name",
            invalid_message="Invalid characters in {field_name}",
        )
        if result is None:
            raise ValueError("Port name cannot be empty")
        return result

    @field_validator("bill_of_lading")
    @classmethod
    def validate_bol(cls, v: str) -> str:
        """Validate bill of lading for XSS prevention."""
        if not v or not v.strip():
            raise ValueError("Bill of lading cannot be empty")
        result = validate_text_field(
            v,
            field_name="bill of lading",
            invalid_message="Invalid characters in {field_name}",
        )
        if result is None:
            raise ValueError("Bill of lading cannot be empty")
        return result

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        """Validate notes for XSS prevention."""
        return validate_text_field(
            v, field_name="notes", invalid_message="Invalid characters in {field_name}"
        )


class ShipmentUpdate(BaseModel):
    current_location: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = None
    actual_arrival: Optional[str] = None
    delay_hours: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("current_location")
    @classmethod
    def validate_current_location(cls, v: Optional[str]) -> Optional[str]:
        """Validate current location for XSS prevention."""
        return validate_text_field(
            v,
            field_name="current location",
            invalid_message="Invalid characters in {field_name}",
        )

    @field_validator("notes")
    @classmethod
    def validate_notes_update(cls, v: Optional[str]) -> Optional[str]:
        """Validate notes for XSS prevention."""
        return validate_text_field(
            v, field_name="notes", invalid_message="Invalid characters in {field_name}"
        )


class TrackingEventCreate(BaseModel):
    timestamp: str
    location: str = Field(..., max_length=200)
    event: str = Field(..., max_length=100)
    details: Optional[str] = Field(None, max_length=500)

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str) -> str:
        """Validate location for XSS prevention."""
        if not v or not v.strip():
            raise ValueError("Location cannot be empty")
        result = validate_text_field(
            v,
            field_name="location",
            invalid_message="Invalid characters in {field_name}",
        )
        if result is None:
            raise ValueError("Location cannot be empty")
        return result

    @field_validator("event")
    @classmethod
    def validate_event(cls, v: str) -> str:
        """Validate event for XSS prevention."""
        if not v or not v.strip():
            raise ValueError("Event cannot be empty")
        result = validate_text_field(
            v,
            field_name="event",
            invalid_message="Invalid characters in {field_name}",
        )
        if result is None:
            raise ValueError("Event cannot be empty")
        return result

    @field_validator("details")
    @classmethod
    def validate_details(cls, v: Optional[str]) -> Optional[str]:
        """Validate details for XSS prevention."""
        return validate_text_field(
            v,
            field_name="details",
            invalid_message="Invalid characters in {field_name}",
        )


class ShipmentOut(BaseModel):
    id: int
    lot_id: Optional[int]
    cooperative_id: Optional[int]
    roaster_id: Optional[int]
    container_number: str
    bill_of_lading: str
    weight_kg: float
    container_type: str
    origin_port: str
    destination_port: str
    current_location: Optional[str]
    departure_date: Optional[str]
    estimated_arrival: Optional[str]
    actual_arrival: Optional[str]
    status: str
    status_updated_at: Optional[str]
    delay_hours: int
    tracking_events: Optional[List[TrackingEvent]] = None
    notes: Optional[str]

    class Config:
        from_attributes = True
