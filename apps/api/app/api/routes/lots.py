from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.api.response_utils import apply_create_status
from app.db.session import get_db
from app.models.lot import Lot
from app.models.user import User
from app.schemas.lot import LotCreate, LotOut, LotUpdate
from app.core.audit import AuditLogger
from app.core.versioning import capture_entity_version
from app.services.data_quality import recompute_entity_flags, resolve_entity_flags

router = APIRouter()


@router.get("/", response_model=list[LotOut])
def list_lots(
    cooperative_id: int | None = None,
    include_deleted: bool = Query(False),
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
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
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "analyst")),
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


@router.get("/{lot_id}", response_model=LotOut)
def get_lot(
    lot_id: int,
    include_deleted: bool = Query(False),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    q = db.query(Lot).filter(Lot.id == lot_id)
    if not include_deleted:
        q = q.filter(Lot.deleted_at.is_(None))
    lot = q.first()
    if not lot:
        raise HTTPException(status_code=404, detail="Not found")
    return lot


@router.patch("/{lot_id}", response_model=LotOut)
def update_lot(
    lot_id: int,
    payload: LotUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "analyst")),
):
    lot = db.query(Lot).filter(Lot.id == lot_id, Lot.deleted_at.is_(None)).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Not found")

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


@router.delete("/{lot_id}")
def delete_lot(
    lot_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Not found")

    # Capture data before deletion for audit log
    entity_data = {
        "name": lot.name,
        "cooperative_id": lot.cooperative_id,
        "weight_kg": lot.weight_kg,
    }

    lot.deleted_at = datetime.utcnow()
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


@router.post("/{lot_id}/restore")
def restore_lot(
    lot_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Not found")

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
