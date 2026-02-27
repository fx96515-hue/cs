from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.source import Source
from app.models.user import User
from app.schemas.source import SourceCreate, SourceOut, SourceUpdate
from app.core.audit import AuditLogger

router = APIRouter()


@router.get("/", response_model=list[SourceOut])
def list_sources(
    db: Session = Depends(get_db), _=Depends(require_role("admin", "analyst", "viewer"))
):
    return db.query(Source).order_by(Source.name.asc()).all()


@router.post("/", response_model=SourceOut)
def create_source(
    payload: SourceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "analyst")),
):
    s = Source(**payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)

    # Log creation for audit trail
    AuditLogger.log_create(
        db=db,
        user=user,
        entity_type="source",
        entity_id=s.id,
        entity_data=payload.model_dump(),
    )

    return s


@router.get("/{source_id}", response_model=SourceOut)
def get_source(
    source_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    s = db.query(Source).filter(Source.id == source_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Not found")
    return s


@router.patch("/{source_id}", response_model=SourceOut)
def update_source(
    source_id: int,
    payload: SourceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "analyst")),
):
    s = db.query(Source).filter(Source.id == source_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Not found")

    # Capture old data for audit log
    old_data = {k: getattr(s, k) for k in payload.model_dump(exclude_unset=True).keys()}

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)

    # Log update for audit trail
    AuditLogger.log_update(
        db=db,
        user=user,
        entity_type="source",
        entity_id=source_id,
        old_data=old_data,
        new_data=payload.model_dump(exclude_unset=True),
    )

    return s


@router.delete("/{source_id}")
def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    s = db.query(Source).filter(Source.id == source_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Not found")

    # Capture data before deletion for audit log
    entity_data = {
        "name": s.name,
        "url": s.url,
    }

    db.delete(s)
    db.commit()

    # Log deletion for audit trail
    AuditLogger.log_delete(
        db=db,
        user=user,
        entity_type="source",
        entity_id=source_id,
        entity_data=entity_data,
    )

    return {"status": "deleted"}
