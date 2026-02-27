from pydantic import BaseModel, Field


class EnrichRequest(BaseModel):
    url: str | None = Field(None, description="Override URL to fetch")
    use_llm: bool = Field(
        True, description="Use Perplexity to extract structured fields (if API key set)"
    )


class EnrichResponse(BaseModel):
    status: str
    entity_type: str
    entity_id: int
    url: str
    web_extract_id: int | None = None
    updated_fields: list[str] = []
    used_llm: bool = False
    error: str | None = None
