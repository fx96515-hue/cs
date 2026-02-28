from fastapi import APIRouter, Depends, HTTPException, Request, Response
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
from app.core.config import settings

router = APIRouter()


@router.get("/", response_model=list[RoasterOut])
def list_roasters(
    db: Session = Depends(get_db), _=Depends(require_role("admin", "analyst", "viewer"))
):
    return db.query(Roaster).order_by(Roaster.name.asc()).all()


@router.post("/", response_model=RoasterOut)
def create_roaster(
    payload: RoasterCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "analyst")),
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


@router.get("/{roaster_id}", response_model=RoasterOut)
def get_roaster(
    roaster_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    r = db.query(Roaster).filter(Roaster.id == roaster_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    return r


@router.patch("/{roaster_id}", response_model=RoasterOut)
def update_roaster(
    roaster_id: int,
    payload: RoasterUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "analyst")),
):
    r = db.query(Roaster).filter(Roaster.id == roaster_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")

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

    # Queue embedding generation task (async, non-blocking)
    if settings.SEMANTIC_SEARCH_ENABLED and settings.EMBEDDING_TASKS_ENABLED:
        try:
            from app.workers.tasks import update_entity_embedding

            update_entity_embedding.delay("roaster", roaster_id)
        except Exception:
            # Graceful degradation - don't fail entity update if task queue fails
            pass

    return r


@router.delete("/{roaster_id}")
def delete_roaster(
    roaster_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    r = db.query(Roaster).filter(Roaster.id == roaster_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")

    # Capture data before deletion for audit log
    entity_data = {
        "name": r.name,
        "city": r.city,
        "website": r.website,
    }

    db.delete(r)
    db.commit()

    # Log deletion for audit trail
    AuditLogger.log_delete(
        db=db,
        user=user,
        entity_type="roaster",
        entity_id=roaster_id,
        entity_data=entity_data,
    )

    return {"status": "deleted"}


@router.get("/export/csv", response_class=StreamingResponse)
def export_roasters_csv(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Export all roasters to CSV format."""
    roasters = db.query(Roaster).order_by(Roaster.name.asc()).all()
    return DataExporter.roasters_to_csv(roasters)
