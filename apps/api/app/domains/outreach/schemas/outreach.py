from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.validation import validate_text_field


class OutreachRequest(BaseModel):
    entity_type: Literal["cooperative", "roaster"]
    entity_id: int = Field(ge=1)
    language: Literal["de", "en", "es"] = "de"
    purpose: Literal["sourcing_pitch", "sample_request"] = "sourcing_pitch"
    counterpart_name: str | None = None
    refine_with_llm: bool = Field(
        False, description="If true and PERPLEXITY_API_KEY is set, polish the text"
    )

    @field_validator("counterpart_name")
    @classmethod
    def validate_counterpart_name(cls, v: str | None) -> str | None:
        return validate_text_field(v, field_name="Ansprechpartner", max_length=120)


class OutreachResponse(BaseModel):
    status: str
    entity_type: str
    entity_id: int
    language: str
    purpose: str
    used_llm: bool
    text: str
