from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.cooperative import Cooperative
from app.models.user import User
from app.schemas.cooperative import CooperativeCreate, CooperativeOut, CooperativeUpdate
from app.services.scoring import recompute_and_persist_cooperative
from app.core.export import DataExporter
from app.core.audit import AuditLogger

router = APIRouter()


@router.get("/", response_model=list[CooperativeOut])
def list_coops(
    db: Session = Depends(get_db), _=Depends(require_role("admin", "analyst", "viewer"))
):
    return db.query(Cooperative).order_by(Cooperative.name.asc()).all()


@router.post("/", response_model=CooperativeOut)
def create_coop(
    payload: CooperativeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "analyst")),
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

    # Queue embedding generation task (async, non-blocking)
    try:
        from app.workers.tasks import update_entity_embedding

        update_entity_embedding.delay("cooperative", coop.id)
    except Exception:
        # Graceful degradation - don't fail entity creation if task queue fails
        pass

    return coop


@router.get("/{coop_id}", response_model=CooperativeOut)
def get_coop(
    coop_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="Not found")
    return coop


@router.patch("/{coop_id}", response_model=CooperativeOut)
def update_coop(
    coop_id: int,
    payload: CooperativeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "analyst")),
):
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="Not found")

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

    # Queue embedding generation task (async, non-blocking)
    try:
        from app.workers.tasks import update_entity_embedding

        update_entity_embedding.delay("cooperative", coop_id)
    except Exception:
        # Graceful degradation - don't fail entity update if task queue fails
        pass

    return coop


@router.delete("/{coop_id}")
def delete_coop(
    coop_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="Not found")

    # Capture data before deletion for audit log
    entity_data = {
        "name": coop.name,
        "region": coop.region,
        "status": coop.status,
    }

    db.delete(coop)
    db.commit()

    # Log deletion for audit trail
    AuditLogger.log_delete(
        db=db,
        user=user,
        entity_type="cooperative",
        entity_id=coop_id,
        entity_data=entity_data,
    )

    return {"status": "deleted"}


@router.post("/{coop_id}/recompute_score")
def recompute_score(
    coop_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()
    if not coop:
        raise HTTPException(status_code=404, detail="Not found")
    breakdown = recompute_and_persist_cooperative(db, coop)
    return {"status": "ok", "coop_id": coop_id, "breakdown": breakdown.__dict__}


@router.get("/export/csv", response_class=StreamingResponse)
def export_cooperatives_csv(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Export all cooperatives to CSV format."""
    cooperatives = db.query(Cooperative).order_by(Cooperative.name.asc()).all()
    return DataExporter.cooperatives_to_csv(cooperatives)
