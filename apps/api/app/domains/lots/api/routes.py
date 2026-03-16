from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.api.response_utils import apply_create_status
from app.core.audit import AuditLogger
from app.core.versioning import capture_entity_version
from app.db.session import get_db
from app.models.lot import Lot
from app.models.user import User
from app.schemas.lot import LotCreate, LotOut, LotUpdate
from app.domains.data_quality.services.flags import recompute_entity_flags, resolve_entity_flags

router = APIRouter()
NOT_FOUND_DETAIL = "Not found"
NOT_FOUND_RESPONSE: dict[int | str, dict[str, Any]] = {
    404: {"description": NOT_FOUND_DETAIL}
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/", response_model=list[LotOut])
def list_lots(
    cooperative_id: Annotated[int | None, Query(ge=1)] = None,
    include_deleted: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    *,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    q = db.query(Lot)
    if not include_deleted:
        q = q.filter(Lot.deleted_at.is_(None))
    if cooperative_id is not None:
        q = q.filter(Lot.cooperative_id == cooperative_id)
    return q.order_by(Lot.created_at.desc()).limit(limit).all()


@router.post("/", response_model=LotOut)
def create_lot(
    payload: LotCreate,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin", "analyst"))],
):
    lot = Lot(**payload.model_dump())
    db.add(lot)
    db.commit()
    db.refresh(lot)

    # Log creation for audit trail
    AuditLogger.log_create(
        db=db,
        user=user,
        entity_type="lot",
        entity_id=lot.id,
        entity_data=payload.model_dump(),
    )
    capture_entity_version(
        db=db,
        entity_type="lot",
        entity_id=lot.id,
        instance=lot,
        user=user,
        reason="create",
    )
    recompute_entity_flags(
        db=db,
        entity_type="lot",
        entity_id=lot.id,
        instance=lot,
        user=user,
    )

    apply_create_status(request, response, created=True)

    return lot


@router.get("/{lot_id}", response_model=LotOut, responses=NOT_FOUND_RESPONSE)
def get_lot(
    lot_id: Annotated[int, Path(ge=1)],
    include_deleted: Annotated[bool, Query()] = False,
    *,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    q = db.query(Lot).filter(Lot.id == lot_id)
    if not include_deleted:
        q = q.filter(Lot.deleted_at.is_(None))
    lot = q.first()
    if not lot:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return lot


@router.patch("/{lot_id}", response_model=LotOut, responses=NOT_FOUND_RESPONSE)
def update_lot(
    lot_id: Annotated[int, Path(ge=1)],
    payload: LotUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin", "analyst"))],
):
    lot = db.query(Lot).filter(Lot.id == lot_id, Lot.deleted_at.is_(None)).first()
    if not lot:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    # Capture old data for audit log
    old_data = {
        k: getattr(lot, k) for k in payload.model_dump(exclude_unset=True).keys()
    }

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(lot, k, v)
    db.commit()
    db.refresh(lot)

    # Log update for audit trail
    AuditLogger.log_update(
        db=db,
        user=user,
        entity_type="lot",
        entity_id=lot_id,
        old_data=old_data,
        new_data=payload.model_dump(exclude_unset=True),
    )
    capture_entity_version(
        db=db,
        entity_type="lot",
        entity_id=lot_id,
        instance=lot,
        user=user,
        reason="update",
    )
    recompute_entity_flags(
        db=db,
        entity_type="lot",
        entity_id=lot_id,
        instance=lot,
        user=user,
    )

    return lot


@router.delete("/{lot_id}", responses=NOT_FOUND_RESPONSE)
def delete_lot(
    lot_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin"))],
):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    # Capture data before deletion for audit log
    entity_data = {
        "name": lot.name,
        "cooperative_id": lot.cooperative_id,
        "weight_kg": lot.weight_kg,
    }

    lot.deleted_at = _utcnow()
    db.commit()

    # Log deletion for audit trail
    AuditLogger.log_delete(
        db=db, user=user, entity_type="lot", entity_id=lot_id, entity_data=entity_data
    )
    capture_entity_version(
        db=db,
        entity_type="lot",
        entity_id=lot_id,
        instance=lot,
        user=user,
        reason="soft_delete",
    )
    resolve_entity_flags(
        db=db,
        entity_type="lot",
        entity_id=lot_id,
        user=user,
    )

    return {"status": "deleted"}


@router.post("/{lot_id}/restore", responses=NOT_FOUND_RESPONSE)
def restore_lot(
    lot_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin"))],
):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    lot.deleted_at = None
    db.commit()
    db.refresh(lot)

    AuditLogger.log_update(
        db=db,
        user=user,
        entity_type="lot",
        entity_id=lot_id,
        old_data={"deleted_at": "set"},
        new_data={"deleted_at": None},
    )
    capture_entity_version(
        db=db,
        entity_type="lot",
        entity_id=lot_id,
        instance=lot,
        user=user,
        reason="restore",
    )
    recompute_entity_flags(
        db=db,
        entity_type="lot",
        entity_id=lot_id,
        instance=lot,
        user=user,
    )

    return lot
