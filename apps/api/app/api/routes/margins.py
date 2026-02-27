from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.margin import MarginRun
from app.models.lot import Lot
from app.schemas.margin import MarginCalcRequest, MarginCalcResult, MarginRunOut
from app.services.margins import calc_margin

router = APIRouter()


@router.post("/calc", response_model=MarginCalcResult)
def calc(payload: MarginCalcRequest, _=Depends(require_role("admin", "analyst"))):
    inputs, outputs = calc_margin(payload)
    return MarginCalcResult(
        computed_at=datetime.now(timezone.utc), inputs=inputs, outputs=outputs
    )


@router.post("/lots/{lot_id}/runs", response_model=MarginRunOut)
def calc_and_store_for_lot(
    lot_id: int,
    payload: MarginCalcRequest,
    profile: str = "conservative",
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    inputs, outputs = calc_margin(payload)
    now = datetime.now(timezone.utc)
    run = MarginRun(
        lot_id=lot_id, profile=profile, inputs=inputs, outputs=outputs, computed_at=now
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("/lots/{lot_id}/runs", response_model=list[MarginRunOut])
def list_runs(
    lot_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    return (
        db.query(MarginRun)
        .filter(MarginRun.lot_id == lot_id)
        .order_by(MarginRun.computed_at.desc())
        .limit(limit)
        .all()
    )
