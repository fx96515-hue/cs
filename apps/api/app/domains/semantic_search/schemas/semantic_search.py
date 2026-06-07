"""Schemas for semantic search functionality."""

from pydantic import BaseModel, Field
from typing import Literal


class SemanticSearchParams(BaseModel):
    """Parameters for semantic search."""

    q: str = Field(min_length=1, max_length=500, description="Search query text")
    entity_type: Literal["cooperative", "roaster", "all"] = Field(
        default="all", description="Type of entity to search"
    )
    limit: int = Field(default=10, ge=1, le=50, description="Max results to return")


class SemanticSearchResult(BaseModel):
    """Single search result with similarity score."""

    entity_type: str
    entity_id: int
    name: str
    similarity_score: float = Field(
        ge=0.0, le=1.0, description="Cosine similarity (0-1, higher is better)"
    )
    # Include key fields for preview
    region: str | None = None
    city: str | None = None
    certifications: str | None = None
    total_score: float | None = None


class SemanticSearchResponse(BaseModel):
    """Response for semantic search."""

    query: str
    entity_type: str
    results: list[SemanticSearchResult]
    total: int


class SimilarEntityResult(BaseModel):
    """Similar entity result."""

    entity_id: int
    name: str
    similarity_score: float = Field(
        ge=0.0, le=1.0, description="Cosine similarity (0-1, higher is better)"
    )
    # Include key fields for preview
    region: str | None = None
    city: str | None = None
    certifications: str | None = None
    total_score: float | None = None


class SimilarEntityResponse(BaseModel):
    """Response for similar entities endpoint."""

    entity_type: str
    entity_id: int
    entity_name: str
    similar_entities: list[SimilarEntityResult]
    total: int
