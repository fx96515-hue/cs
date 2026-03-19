from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.api.response_utils import apply_create_status
from app.core.idempotency import find_existing_by_fields
from app.db.session import get_db
from app.models.source import Source
from app.models.user import User
from app.domains.sources.schemas.source import SourceCreate, SourceOut, SourceUpdate
from app.core.audit import AuditLogger

router = APIRouter()
DbSessionDep = Annotated[Session, Depends(get_db)]
ViewerPermissionDep = Annotated[
    None, Depends(require_role("admin", "analyst", "viewer"))
]
AnalystUserDep = Annotated[User, Depends(require_role("admin", "analyst"))]
AdminUserDep = Annotated[User, Depends(require_role("admin"))]
NOT_FOUND_DETAIL = "Not found"


@router.get("/", response_model=list[SourceOut])
def list_sources(
    db: DbSessionDep,
    _: ViewerPermissionDep,
):
    return db.query(Source).order_by(Source.name.asc()).all()


@router.post("/", response_model=SourceOut)
def create_source(
    payload: SourceCreate,
    request: Request,
    response: Response,
    db: DbSessionDep,
    user: AnalystUserDep,
):
    existing = find_existing_by_fields(
        db,
        Source,
        {"name": payload.name, "url": payload.url, "kind": payload.kind},
    )
    if existing:
        apply_create_status(request, response, created=False)
        return existing

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

    apply_create_status(request, response, created=True)

    return s


@router.get(
    "/{source_id}",
    response_model=SourceOut,
    responses={404: {"description": "Source not found"}},
)
def get_source(
    source_id: Annotated[int, Path(ge=1)],
    db: DbSessionDep,
    _: ViewerPermissionDep,
):
    s = db.query(Source).filter(Source.id == source_id).first()
    if not s:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return s


@router.patch(
    "/{source_id}",
    response_model=SourceOut,
    responses={404: {"description": "Source not found"}},
)
def update_source(
    source_id: Annotated[int, Path(ge=1)],
    payload: SourceUpdate,
    db: DbSessionDep,
    user: AnalystUserDep,
):
    s = db.query(Source).filter(Source.id == source_id).first()
    if not s:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

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


@router.delete(
    "/{source_id}",
    responses={404: {"description": "Source not found"}},
)
def delete_source(
    source_id: Annotated[int, Path(ge=1)],
    db: DbSessionDep,
    user: AdminUserDep,
):
    s = db.query(Source).filter(Source.id == source_id).first()
    if not s:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

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
