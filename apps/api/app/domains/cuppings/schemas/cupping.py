from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.validation import validate_text_field


class CuppingCreate(BaseModel):
    occurred_at: datetime | None = None
    taster: str | None = Field(None, max_length=255)
    cooperative_id: int | None = Field(None, gt=0)
    lot_id: int | None = Field(None, gt=0)
    roaster_id: int | None = Field(None, gt=0)

    sca_score: float | None = Field(None, ge=0, le=100)
    aroma: float | None = Field(None, ge=0, le=10)
    flavor: float | None = Field(None, ge=0, le=10)
    aftertaste: float | None = Field(None, ge=0, le=10)
    acidity: float | None = Field(None, ge=0, le=10)
    body: float | None = Field(None, ge=0, le=10)
    balance: float | None = Field(None, ge=0, le=10)
    sweetness: float | None = Field(None, ge=0, le=10)
    uniformity: float | None = Field(None, ge=0, le=10)
    clean_cup: float | None = Field(None, ge=0, le=10)

    descriptors: str | None = Field(None, max_length=1000)
    defects: str | None = Field(None, max_length=1000)
    notes: str | None = None
    meta: dict | None = None

    @field_validator("taster")
    @classmethod
    def validate_taster(cls, v: str | None) -> str | None:
        """Validate taster name for XSS prevention."""
        return validate_text_field(
            v, field_name="taster name", required=False, max_length=255
        )


class CuppingOut(CuppingCreate):
    id: int

    class Config:
        from_attributes = True
