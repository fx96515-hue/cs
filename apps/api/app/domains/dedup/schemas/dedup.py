from typing import Literal

from pydantic import BaseModel
from pydantic import Field


class DedupPairOut(BaseModel):
    a_id: int
    b_id: int
    a_name: str
    b_name: str
    score: float
    reason: str


class MergeEntitiesIn(BaseModel):
    """Request to merge two entities."""

    entity_type: Literal["cooperative", "roaster"]
    keep_id: int = Field(ge=1)
    merge_id: int = Field(ge=1)


class MergeResultOut(BaseModel):
    """Result of merge operation."""

    status: str
    entity_type: str
    keep_id: int
    merge_id: int
    merged_fields: list[str]
    alias_created: str


class MergeHistoryOut(BaseModel):
    """Merge history entry."""

    entity_id: int
    created_at: str
    payload: dict
