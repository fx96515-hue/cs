from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.api.response_utils import apply_create_status
from app.db.session import get_db
from app.models.cupping import CuppingResult
from app.schemas.cupping import CuppingCreate, CuppingOut


router = APIRouter()


@router.get("/", response_model=list[CuppingOut])
def list_cuppings(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
):
    return (
        db.query(CuppingResult)
        .order_by(CuppingResult.occurred_at.desc().nullslast())
        .limit(limit)
        .all()
    )


@router.post("/", response_model=CuppingOut)
def create(
    payload: CuppingCreate,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
):
    row = CuppingResult(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    apply_create_status(request, response, created=True)
    return row
