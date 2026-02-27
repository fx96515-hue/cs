from pydantic import BaseModel


class DedupPairOut(BaseModel):
    a_id: int
    b_id: int
    a_name: str
    b_name: str
    score: float
    reason: str


class MergeEntitiesIn(BaseModel):
    """Request to merge two entities."""

    entity_type: str
    keep_id: int
    merge_id: int


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
