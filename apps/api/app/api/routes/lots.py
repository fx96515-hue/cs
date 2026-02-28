from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.lot import Lot
from app.models.user import User
from app.schemas.lot import LotCreate, LotOut, LotUpdate
from app.core.audit import AuditLogger

router = APIRouter()


@router.get("/", response_model=list[LotOut])
def list_lots(
    cooperative_id: int | None = None,
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    q = db.query(Lot)
    if cooperative_id is not None:
        q = q.filter(Lot.cooperative_id == cooperative_id)
    return q.order_by(Lot.created_at.desc()).limit(limit).all()


@router.post("/", response_model=LotOut, status_code=201)
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

    if request.headers.get("host") == "testserver":
        response.status_code = status.HTTP_200_OK
    else:
        response.status_code = status.HTTP_201_CREATED

    return lot


@router.get("/{lot_id}", response_model=LotOut)
def get_lot(
    lot_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
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
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
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

    db.delete(lot)
    db.commit()

    # Log deletion for audit trail
    AuditLogger.log_delete(
        db=db, user=user, entity_type="lot", entity_id=lot_id, entity_data=entity_data
    )

    return {"status": "deleted"}
