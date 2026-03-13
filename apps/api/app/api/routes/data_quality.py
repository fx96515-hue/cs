from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role, get_db
from app.models.data_quality_flag import DataQualityFlag
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster
from app.models.lot import Lot
from app.models.deal import Deal
from app.models.shipment import Shipment
from app.schemas.data_quality import DataQualityFlagOut
from app.services.data_quality import recompute_entity_flags
from app.models.user import User

router = APIRouter()
NOT_FOUND_DETAIL = "Not found"
UNSUPPORTED_ENTITY_DETAIL = "Unsupported entity_type"
RESOLVE_FLAG_RESPONSES: dict[int | str, dict[str, Any]] = {
    404: {"description": NOT_FOUND_DETAIL}
}
RECOMPUTE_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"description": UNSUPPORTED_ENTITY_DETAIL},
    404: {"description": NOT_FOUND_DETAIL},
}


ENTITY_MODEL_MAP = {
    "cooperative": Cooperative,
    "roaster": Roaster,
    "lot": Lot,
    "shipment": Shipment,
    "deal": Deal,
}


@router.get("/flags", response_model=list[DataQualityFlagOut])
def list_flags(
    entity_type: str | None = None,
    entity_id: int | None = None,
    severity: str | None = None,
    include_resolved: bool = Query(False),
    limit: int = Query(200, ge=1, le=1000),
    *,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_role("admin", "analyst"))],
):
    q = db.query(DataQualityFlag)
    if entity_type:
        q = q.filter(DataQualityFlag.entity_type == entity_type)
    if entity_id:
        q = q.filter(DataQualityFlag.entity_id == entity_id)
    if severity:
        q = q.filter(DataQualityFlag.severity == severity)
    if not include_resolved:
        q = q.filter(DataQualityFlag.resolved_at.is_(None))
    return q.order_by(DataQualityFlag.detected_at.desc()).limit(limit).all()


@router.post(
    "/flags/{flag_id}/resolve",
    response_model=DataQualityFlagOut,
    responses=RESOLVE_FLAG_RESPONSES,
)
def resolve_flag(
    flag_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin", "analyst"))],
):
    flag = db.query(DataQualityFlag).filter(DataQualityFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    flag.resolved_at = flag.resolved_at or datetime.now(timezone.utc)
    flag.resolved_by = user.email
    db.commit()
    db.refresh(flag)
    return flag


@router.post("/recompute/{entity_type}/{entity_id}", responses=RECOMPUTE_RESPONSES)
def recompute_flags(
    entity_type: str,
    entity_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin", "analyst"))],
):
    model = ENTITY_MODEL_MAP.get(entity_type)
    if not model:
        raise HTTPException(status_code=400, detail=UNSUPPORTED_ENTITY_DETAIL)
    model_id_column = getattr(model, "id", None)
    if model_id_column is None:
        raise HTTPException(status_code=400, detail=UNSUPPORTED_ENTITY_DETAIL)
    instance = db.query(model).filter(model_id_column == entity_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    result = recompute_entity_flags(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        instance=instance,
        user=user,
    )
    return {"status": "ok", **result}
