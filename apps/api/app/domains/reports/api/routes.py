from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.report import Report
from app.domains.reports.schemas.report import ReportOut

router = APIRouter()
DbSessionDep = Annotated[Session, Depends(get_db)]
ViewerPermissionDep = Annotated[
    object, Depends(require_role("admin", "analyst", "viewer"))
]


@router.get("/", response_model=list[ReportOut])
def list_reports(
    db: DbSessionDep,
    _: ViewerPermissionDep,
    limit: int = Query(30, ge=1, le=200),
):
    return db.query(Report).order_by(Report.report_at.desc()).limit(limit).all()


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: Annotated[int, Path(ge=1)],
    db: DbSessionDep,
    _: ViewerPermissionDep,
):
    r = db.query(Report).filter(Report.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    return r
