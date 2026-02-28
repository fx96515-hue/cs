from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.schemas.dedup import (
    DedupPairOut,
    MergeEntitiesIn,
    MergeResultOut,
    MergeHistoryOut,
)
from app.services.dedup import suggest_duplicates, merge_entities, get_merge_history


router = APIRouter()


@router.get(
    "/suggest",
    response_model=list[DedupPairOut],
    responses={400: {"description": "Invalid request"}},
)
def suggest(
    entity_type: str,
    threshold: float = 90.0,
    limit: int = Query(50, ge=1, le=200),
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
):
    try:
        return suggest_duplicates(
            db, entity_type=entity_type, threshold=threshold, limit_pairs=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/merge",
    response_model=MergeResultOut,
    responses={400: {"description": "Invalid request"}},
)
def merge(
    payload: MergeEntitiesIn,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin"))],
):
    """Merge two entities."""
    try:
        result = merge_entities(
            db,
            entity_type=payload.entity_type,
            keep_id=payload.keep_id,
            merge_id=payload.merge_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=list[MergeHistoryOut])
def history(
    entity_type: str,
    limit: int = Query(50, ge=1, le=200),
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
):
    """View merge history."""
    return get_merge_history(db, entity_type=entity_type, limit=limit)
