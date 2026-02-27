from pydantic import BaseModel, Field


class OutreachRequest(BaseModel):
    entity_type: str
    entity_id: int
    language: str = "de"
    purpose: str = "sourcing_pitch"
    counterpart_name: str | None = None
    refine_with_llm: bool = Field(
        False, description="If true and PERPLEXITY_API_KEY is set, polish the text"
    )


class OutreachResponse(BaseModel):
    status: str
    entity_type: str
    entity_id: int
    language: str
    purpose: str
    used_llm: bool
    text: str
