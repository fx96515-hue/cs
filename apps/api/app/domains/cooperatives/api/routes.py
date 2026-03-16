from typing import Annotated, Any
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response
from fastapi.responses import StreamingResponse
import structlog
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.api.response_utils import apply_create_status
from app.db.session import get_db
from app.models.cooperative import Cooperative
from app.models.user import User
from app.domains.cooperatives.schemas.cooperative import CooperativeCreate, CooperativeOut, CooperativeUpdate
from app.services.discovery import backfill_missing_cooperative_data
from app.services.scoring import recompute_and_persist_cooperative
from app.core.export import DataExporter
from app.core.audit import AuditLogger
from app.core.versioning import capture_entity_version
from app.domains.data_quality.services.flags import recompute_entity_flags, resolve_entity_flags
from app.core.config import settings

router = APIRouter()
log = structlog.get_logger()

NOT_FOUND_DETAIL = "Not found"
NOT_FOUND_RESPONSES: dict[int | str, dict[str, Any]] = {
    404: {"description": "Cooperative not found"}
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/", response_model=list[CooperativeOut])
def list_coops(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
    include_deleted: Annotated[bool, Query()] = False,
):
    q = db.query(Cooperative)
    if not include_deleted:
        q = q.filter(Cooperative.deleted_at.is_(None))
    return q.order_by(Cooperative.name.asc()).all()


@router.post("/", response_model=CooperativeOut)
def create_coop(
    payload: CooperativeCreate,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin", "analyst"))],
):
    coop = Cooperative(**payload.model_dump())
    db.add(coop)
    db.commit()
    db.refresh(coop)

    # Log creation for audit trail
    AuditLogger.log_create(
        db=db,
        user=user,
        entity_type="cooperative",
        entity_id=coop.id,
        entity_data=payload.model_dump(),
    )
    capture_entity_version(
        db=db,
        entity_type="cooperative",
        entity_id=coop.id,
        instance=coop,
        user=user,
        reason="create",
    )
    recompute_entity_flags(
        db=db,
        entity_type="cooperative",
        entity_id=coop.id,
        instance=coop,
        user=user,
    )

    apply_create_status(request, response, created=True)

    # Queue embedding generation task (async, non-blocking)
    if settings.SEMANTIC_SEARCH_ENABLED and settings.EMBEDDING_TASKS_ENABLED:
        try:
            from app.workers.tasks import update_entity_embedding

            update_entity_embedding.delay("cooperative", coop.id)
        except Exception as exc:
            # Graceful degradation - don't fail entity creation if task queue fails
            log.warning(
                "cooperative_embedding_enqueue_failed",
                coop_id=coop.id,
                error=str(exc),
            )

    return coop


@router.get(
    "/{coop_id}",
    response_model=CooperativeOut,
    responses=NOT_FOUND_RESPONSES,
)
def get_coop(
    coop_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
    include_deleted: Annotated[bool, Query()] = False,
):
    q = db.query(Cooperative).filter(Cooperative.id == coop_id)
    if not include_deleted:
        q = q.filter(Cooperative.deleted_at.is_(None))
    coop = q.first()
    if not coop:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return coop


@router.patch(
    "/{coop_id}",
    response_model=CooperativeOut,
    responses=NOT_FOUND_RESPONSES,
)
def update_coop(
    coop_id: Annotated[int, Path(ge=1)],
    payload: CooperativeUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin", "analyst"))],
):
    coop = (
        db.query(Cooperative)
        .filter(Cooperative.id == coop_id, Cooperative.deleted_at.is_(None))
        .first()
    )
    if not coop:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    # Capture old data for audit log
    old_data = {
        k: getattr(coop, k) for k in payload.model_dump(exclude_unset=True).keys()
    }

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(coop, k, v)
    db.commit()
    db.refresh(coop)

    # Log update for audit trail
    AuditLogger.log_update(
        db=db,
        user=user,
        entity_type="cooperative",
        entity_id=coop_id,
        old_data=old_data,
        new_data=payload.model_dump(exclude_unset=True),
    )
    capture_entity_version(
        db=db,
        entity_type="cooperative",
        entity_id=coop_id,
        instance=coop,
        user=user,
        reason="update",
    )
    recompute_entity_flags(
        db=db,
        entity_type="cooperative",
        entity_id=coop_id,
        instance=coop,
        user=user,
    )

    # Queue embedding generation task (async, non-blocking)
    if settings.SEMANTIC_SEARCH_ENABLED and settings.EMBEDDING_TASKS_ENABLED:
        try:
            from app.workers.tasks import update_entity_embedding

            update_entity_embedding.delay("cooperative", coop_id)
        except Exception as exc:
            # Graceful degradation - don't fail entity update if task queue fails
            log.warning(
                "cooperative_embedding_enqueue_failed",
                coop_id=coop_id,
                error=str(exc),
            )

    return coop


@router.delete(
    "/{coop_id}",
    responses=NOT_FOUND_RESPONSES,
)
def delete_coop(
    coop_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin"))],
):
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    # Capture data before deletion for audit log
    entity_data = {
        "name": coop.name,
        "region": coop.region,
        "status": coop.status,
    }

    coop.deleted_at = _utcnow()
    db.commit()

    # Log deletion for audit trail
    AuditLogger.log_delete(
        db=db,
        user=user,
        entity_type="cooperative",
        entity_id=coop_id,
        entity_data=entity_data,
    )
    capture_entity_version(
        db=db,
        entity_type="cooperative",
        entity_id=coop_id,
        instance=coop,
        user=user,
        reason="soft_delete",
    )
    resolve_entity_flags(
        db=db,
        entity_type="cooperative",
        entity_id=coop_id,
        user=user,
    )

    return {"status": "deleted"}


@router.post(
    "/{coop_id}/restore",
    responses=NOT_FOUND_RESPONSES,
)
def restore_coop(
    coop_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin"))],
):
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    coop.deleted_at = None
    db.commit()
    db.refresh(coop)

    AuditLogger.log_update(
        db=db,
        user=user,
        entity_type="cooperative",
        entity_id=coop_id,
        old_data={"deleted_at": "set"},
        new_data={"deleted_at": None},
    )
    capture_entity_version(
        db=db,
        entity_type="cooperative",
        entity_id=coop_id,
        instance=coop,
        user=user,
        reason="restore",
    )
    recompute_entity_flags(
        db=db,
        entity_type="cooperative",
        entity_id=coop_id,
        instance=coop,
        user=user,
    )

    return coop


@router.post(
    "/{coop_id}/recompute_score",
    responses=NOT_FOUND_RESPONSES,
)
def recompute_score(
    coop_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
):
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    breakdown = recompute_and_persist_cooperative(db, coop)
    return {"status": "ok", "coop_id": coop_id, "breakdown": breakdown.__dict__}


@router.get("/export/csv", response_class=StreamingResponse)
def export_cooperatives_csv(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
    include_deleted: Annotated[bool, Query()] = False,
):
    """Export all cooperatives to CSV format."""
    q = db.query(Cooperative)
    if not include_deleted:
        q = q.filter(Cooperative.deleted_at.is_(None))
    cooperatives = q.order_by(Cooperative.name.asc()).all()
    return DataExporter.cooperatives_to_csv(cooperatives)


@router.post("/backfill-missing")
def backfill_missing_cooperatives(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
    dry_run: bool = False,
):
    """Search and fill missing cooperative fields from discovery provider results."""
    return backfill_missing_cooperative_data(
        db,
        limit=limit,
        dry_run=dry_run,
    )


@router.post(
    "/{coop_id}/backfill-missing",
    responses=NOT_FOUND_RESPONSES,
)
def backfill_single_cooperative(
    coop_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
    dry_run: bool = False,
):
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return backfill_missing_cooperative_data(
        db,
        limit=1,
        dry_run=dry_run,
        cooperative_id=coop_id,
    )
