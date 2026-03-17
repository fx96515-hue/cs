from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.domains.dedup.schemas.dedup import (
    DedupPairOut,
    MergeEntitiesIn,
    MergeResultOut,
    MergeHistoryOut,
)
from app.domains.dedup.services.merge import (
    get_merge_history,
    merge_entities,
    suggest_duplicates,
)


router = APIRouter()


@router.get(
    "/suggest",
    response_model=list[DedupPairOut],
    responses={400: {"description": "Invalid request"}},
)
def suggest(
    entity_type: Annotated[Literal["cooperative", "roaster"], Query()],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[object, Depends(require_role("admin", "analyst"))],
    threshold: Annotated[float, Query(ge=0, le=100)] = 90.0,
    limit: int = Query(50, ge=1, le=200),
):
    try:
        return suggest_duplicates(
            db, entity_type=entity_type, threshold=threshold, limit_pairs=limit
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request")


@router.post(
    "/merge",
    response_model=MergeResultOut,
    responses={400: {"description": "Invalid request"}},
)
def merge(
    payload: MergeEntitiesIn,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[object, Depends(require_role("admin"))],
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
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request")


@router.get("/history", response_model=list[MergeHistoryOut])
def history(
    entity_type: Annotated[Literal["cooperative", "roaster"], Query()],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[object, Depends(require_role("admin", "analyst"))],
    limit: int = Query(50, ge=1, le=200),
):
    """View merge history."""
    return get_merge_history(db, entity_type=entity_type, limit=limit)
