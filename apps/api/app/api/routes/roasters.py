from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.api.response_utils import apply_create_status
from app.db.session import get_db
from app.models.roaster import Roaster
from app.models.user import User
from app.schemas.roaster import RoasterCreate, RoasterOut, RoasterUpdate
from app.core.export import DataExporter
from app.core.audit import AuditLogger
from app.core.versioning import capture_entity_version
from app.domains.data_quality.services.flags import recompute_entity_flags, resolve_entity_flags
from app.core.config import settings

router = APIRouter()
NOT_FOUND_DETAIL = "Not found"
NOT_FOUND_RESPONSE: dict[int | str, dict[str, Any]] = {
    404: {"description": NOT_FOUND_DETAIL}
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/", response_model=list[RoasterOut])
def list_roasters(
    include_deleted: Annotated[bool, Query()] = False,
    *,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    q = db.query(Roaster)
    if not include_deleted:
        q = q.filter(Roaster.deleted_at.is_(None))
    return q.order_by(Roaster.name.asc()).all()


@router.post("/", response_model=RoasterOut)
def create_roaster(
    payload: RoasterCreate,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin", "analyst"))],
):
    r = Roaster(**payload.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)

    # Log creation for audit trail
    AuditLogger.log_create(
        db=db,
        user=user,
        entity_type="roaster",
        entity_id=r.id,
        entity_data=payload.model_dump(),
    )
    capture_entity_version(
        db=db,
        entity_type="roaster",
        entity_id=r.id,
        instance=r,
        user=user,
        reason="create",
    )
    recompute_entity_flags(
        db=db,
        entity_type="roaster",
        entity_id=r.id,
        instance=r,
        user=user,
    )

    apply_create_status(request, response, created=True)

    # Queue embedding generation task (async, non-blocking)
    if settings.SEMANTIC_SEARCH_ENABLED and settings.EMBEDDING_TASKS_ENABLED:
        try:
            from app.workers.tasks import update_entity_embedding

            update_entity_embedding.delay("roaster", r.id)
        except Exception:
            # Graceful degradation - don't fail entity creation if task queue fails
            pass

    return r


@router.get("/{roaster_id}", response_model=RoasterOut, responses=NOT_FOUND_RESPONSE)
def get_roaster(
    roaster_id: Annotated[int, Path(ge=1)],
    include_deleted: Annotated[bool, Query()] = False,
    *,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    q = db.query(Roaster).filter(Roaster.id == roaster_id)
    if not include_deleted:
        q = q.filter(Roaster.deleted_at.is_(None))
    r = q.first()
    if not r:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return r


@router.patch("/{roaster_id}", response_model=RoasterOut, responses=NOT_FOUND_RESPONSE)
def update_roaster(
    roaster_id: Annotated[int, Path(ge=1)],
    payload: RoasterUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin", "analyst"))],
):
    r = (
        db.query(Roaster)
        .filter(Roaster.id == roaster_id, Roaster.deleted_at.is_(None))
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    # Capture old data for audit log
    old_data = {k: getattr(r, k) for k in payload.model_dump(exclude_unset=True).keys()}

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)

    # Log update for audit trail
    AuditLogger.log_update(
        db=db,
        user=user,
        entity_type="roaster",
        entity_id=roaster_id,
        old_data=old_data,
        new_data=payload.model_dump(exclude_unset=True),
    )
    capture_entity_version(
        db=db,
        entity_type="roaster",
        entity_id=roaster_id,
        instance=r,
        user=user,
        reason="update",
    )
    recompute_entity_flags(
        db=db,
        entity_type="roaster",
        entity_id=roaster_id,
        instance=r,
        user=user,
    )

    # Queue embedding generation task (async, non-blocking)
    if settings.SEMANTIC_SEARCH_ENABLED and settings.EMBEDDING_TASKS_ENABLED:
        try:
            from app.workers.tasks import update_entity_embedding

            update_entity_embedding.delay("roaster", roaster_id)
        except Exception:
            # Graceful degradation - don't fail entity update if task queue fails
            pass

    return r


@router.delete("/{roaster_id}", responses=NOT_FOUND_RESPONSE)
def delete_roaster(
    roaster_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin"))],
):
    r = db.query(Roaster).filter(Roaster.id == roaster_id).first()
    if not r:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    # Capture data before deletion for audit log
    entity_data = {
        "name": r.name,
        "city": r.city,
        "website": r.website,
    }

    r.deleted_at = _utcnow()
    db.commit()

    # Log deletion for audit trail
    AuditLogger.log_delete(
        db=db,
        user=user,
        entity_type="roaster",
        entity_id=roaster_id,
        entity_data=entity_data,
    )
    capture_entity_version(
        db=db,
        entity_type="roaster",
        entity_id=roaster_id,
        instance=r,
        user=user,
        reason="soft_delete",
    )
    resolve_entity_flags(
        db=db,
        entity_type="roaster",
        entity_id=roaster_id,
        user=user,
    )

    return {"status": "deleted"}


@router.post("/{roaster_id}/restore", responses=NOT_FOUND_RESPONSE)
def restore_roaster(
    roaster_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin"))],
):
    r = db.query(Roaster).filter(Roaster.id == roaster_id).first()
    if not r:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    r.deleted_at = None
    db.commit()
    db.refresh(r)

    AuditLogger.log_update(
        db=db,
        user=user,
        entity_type="roaster",
        entity_id=roaster_id,
        old_data={"deleted_at": "set"},
        new_data={"deleted_at": None},
    )
    capture_entity_version(
        db=db,
        entity_type="roaster",
        entity_id=roaster_id,
        instance=r,
        user=user,
        reason="restore",
    )
    recompute_entity_flags(
        db=db,
        entity_type="roaster",
        entity_id=roaster_id,
        instance=r,
        user=user,
    )

    return r


@router.get("/export/csv", response_class=StreamingResponse)
def export_roasters_csv(
    include_deleted: Annotated[bool, Query()] = False,
    *,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    """Export all roasters to CSV format."""
    q = db.query(Roaster)
    if not include_deleted:
        q = q.filter(Roaster.deleted_at.is_(None))
    roasters = q.order_by(Roaster.name.asc()).all()
    return DataExporter.roasters_to_csv(roasters)
