from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


class RoasterCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    city: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    contact_email: Optional[EmailStr] = None
    peru_focus: bool = False
    specialty_focus: bool = True
    price_position: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    status: Optional[str] = Field("active", max_length=32)
    next_action: Optional[str] = Field(None, max_length=255)
    requested_data: Optional[str] = None
    meta: Optional[dict] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate roaster name for XSS prevention."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        # Prevent XSS attempts
        if any(
            pattern in v.lower() for pattern in ["<script", "<iframe", "javascript:"]
        ):
            raise ValueError("Invalid characters in name")
        return v.strip()

    @field_validator("website")
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        """Validate website URL format."""
        if v and v.strip():
            v = v.strip()
            # Must be a valid http/https URL
            if not (v.startswith("http://") or v.startswith("https://")):
                raise ValueError("Website must start with http:// or https://")
            # Basic URL validation - prevent javascript: and other dangerous protocols
            if any(proto in v.lower() for proto in ["javascript:", "data:", "file:"]):
                raise ValueError("Invalid URL protocol")
        return v if v else None

    @field_validator("price_position")
    @classmethod
    def validate_price_position(cls, v: Optional[str]) -> Optional[str]:
        """Validate price position values."""
        if v is None:
            return v
        valid_positions = ["premium", "mid-range", "value", "luxury"]
        v_lower = v.lower().strip()
        if v_lower not in valid_positions:
            raise ValueError(f"Price position must be one of {valid_positions}")
        return v_lower

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status values."""
        if v is None:
            return "active"
        valid_statuses = ["active", "inactive", "prospect", "archived"]
        v_lower = v.lower().strip()
        if v_lower not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v_lower


class RoasterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    city: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    contact_email: Optional[EmailStr] = None
    peru_focus: Optional[bool] = None
    specialty_focus: Optional[bool] = None
    price_position: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    status: Optional[str] = Field(None, max_length=32)
    next_action: Optional[str] = Field(None, max_length=255)
    requested_data: Optional[str] = None
    last_verified_at: Optional[datetime] = None
    total_score: Optional[float] = Field(None, ge=0, le=100)
    confidence: Optional[float] = Field(None, ge=0, le=1)
    meta: Optional[dict] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate roaster name for XSS prevention."""
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

    @field_validator("website")
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        """Validate website URL format."""
        if v and v.strip():
            v = v.strip()
            # Must be a valid http/https URL
            if not (v.startswith("http://") or v.startswith("https://")):
                raise ValueError("Website must start with http:// or https://")
            # Basic URL validation - prevent javascript: and other dangerous protocols
            if any(proto in v.lower() for proto in ["javascript:", "data:", "file:"]):
                raise ValueError("Invalid URL protocol")
        return v if v else None

    @field_validator("price_position")
    @classmethod
    def validate_price_position(cls, v: Optional[str]) -> Optional[str]:
        """Validate price position values."""
        if v is None:
            return v
        valid_positions = ["premium", "mid-range", "value", "luxury"]
        v_lower = v.lower().strip()
        if v_lower not in valid_positions:
            raise ValueError(f"Price position must be one of {valid_positions}")
        return v_lower

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status values."""
        if v is None:
            return v
        valid_statuses = ["active", "inactive", "prospect", "archived"]
        v_lower = v.lower().strip()
        if v_lower not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v_lower


class RoasterOut(BaseModel):
    id: int
    name: str
    city: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    peru_focus: bool
    specialty_focus: bool
    price_position: Optional[str] = None
    notes: Optional[str] = None

    status: str
    next_action: Optional[str] = None
    requested_data: Optional[str] = None
    last_verified_at: Optional[datetime] = None
    total_score: Optional[float] = None
    confidence: Optional[float] = None
    last_scored_at: Optional[datetime] = None
    meta: Optional[dict] = None

    class Config:
        from_attributes = True
