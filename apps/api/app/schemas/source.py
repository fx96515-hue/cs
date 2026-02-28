from pydantic import BaseModel, field_validator
from typing import Optional

from app.core.validation import validate_text_field, validate_url_field


class SourceCreate(BaseModel):
    name: str
    url: Optional[str] = None
    kind: str = "web"
    reliability: Optional[float] = None
    notes: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_text_field(v, field_name="Name", required=True)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        return validate_url_field(v, field_name="URL")

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        return validate_text_field(v, field_name="Notizen")


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    kind: Optional[str] = None
    reliability: Optional[float] = None
    notes: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_text_field(v, field_name="Name", required=True)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        return validate_url_field(v, field_name="URL")

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        return validate_text_field(v, field_name="Notizen")


class SourceOut(BaseModel):
    id: int
    name: str
    url: Optional[str] = None
    kind: str
    reliability: Optional[float] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True
