from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.api.response_utils import apply_create_status
from app.core.audit import AuditLogger
from app.core.versioning import capture_entity_version
from app.db.session import get_db
from app.models.deal import Deal
from app.models.user import User
from app.domains.deals.schemas.deal import DealCreate, DealOut, DealUpdate
from app.domains.data_quality.services.flags import (
    recompute_entity_flags,
    resolve_entity_flags,
)

router = APIRouter()
DEAL_STATUS_QUERY_PATTERN = r"^(open|in_progress|closed|canceled)$"
NOT_FOUND_DETAIL = "Not found"
NOT_FOUND_RESPONSE: dict[int | str, dict[str, Any]] = {
    404: {"description": NOT_FOUND_DETAIL}
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _apply_value_fallbacks(deal: Deal) -> None:
    if deal.value_total is None and deal.price_per_kg and deal.weight_kg:
        deal.value_total = deal.price_per_kg * deal.weight_kg
    if (
        deal.value_eur is None
        and deal.currency == "EUR"
        and deal.value_total is not None
    ):
        deal.value_eur = deal.value_total


@router.get("/", response_model=list[DealOut])
def list_deals(
    cooperative_id: Annotated[int | None, Query(ge=1)] = None,
    roaster_id: Annotated[int | None, Query(ge=1)] = None,
    lot_id: Annotated[int | None, Query(ge=1)] = None,
    status: Annotated[str | None, Query(pattern=DEAL_STATUS_QUERY_PATTERN)] = None,
    include_deleted: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    *,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    q = db.query(Deal)
    if not include_deleted:
        q = q.filter(Deal.deleted_at.is_(None))
    if cooperative_id is not None:
        q = q.filter(Deal.cooperative_id == cooperative_id)
    if roaster_id is not None:
        q = q.filter(Deal.roaster_id == roaster_id)
    if lot_id is not None:
        q = q.filter(Deal.lot_id == lot_id)
    if status:
        q = q.filter(Deal.status == status)
    return q.order_by(Deal.created_at.desc()).limit(limit).all()


@router.post("/", response_model=DealOut)
def create_deal(
    payload: DealCreate,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin", "analyst"))],
):
    deal = Deal(**payload.model_dump())
    if deal.status == "closed" and deal.closed_at is None:
        deal.closed_at = _utcnow()
    _apply_value_fallbacks(deal)
    db.add(deal)
    db.commit()
    db.refresh(deal)

    AuditLogger.log_create(
        db=db,
        user=user,
        entity_type="deal",
        entity_id=deal.id,
        entity_data=payload.model_dump(),
    )
    capture_entity_version(
        db=db,
        entity_type="deal",
        entity_id=deal.id,
        instance=deal,
        user=user,
        reason="create",
    )
    recompute_entity_flags(
        db=db,
        entity_type="deal",
        entity_id=deal.id,
        instance=deal,
        user=user,
    )

    apply_create_status(request, response, created=True)

    return deal


@router.get("/{deal_id}", response_model=DealOut, responses=NOT_FOUND_RESPONSE)
def get_deal(
    deal_id: Annotated[int, Path(ge=1)],
    include_deleted: Annotated[bool, Query()] = False,
    *,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    q = db.query(Deal).filter(Deal.id == deal_id)
    if not include_deleted:
        q = q.filter(Deal.deleted_at.is_(None))
    deal = q.first()
    if not deal:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return deal


@router.patch("/{deal_id}", response_model=DealOut, responses=NOT_FOUND_RESPONSE)
def update_deal(
    deal_id: Annotated[int, Path(ge=1)],
    payload: DealUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin", "analyst"))],
):
    deal = db.query(Deal).filter(Deal.id == deal_id, Deal.deleted_at.is_(None)).first()
    if not deal:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    old_data = {
        k: getattr(deal, k) for k in payload.model_dump(exclude_unset=True).keys()
    }

    update_dict = payload.model_dump(exclude_unset=True)
    if "status" in update_dict and update_dict["status"] == "closed":
        update_dict.setdefault("closed_at", _utcnow())
    for k, v in update_dict.items():
        setattr(deal, k, v)
    _apply_value_fallbacks(deal)

    db.commit()
    db.refresh(deal)

    AuditLogger.log_update(
        db=db,
        user=user,
        entity_type="deal",
        entity_id=deal_id,
        old_data=old_data,
        new_data=payload.model_dump(exclude_unset=True),
    )
    capture_entity_version(
        db=db,
        entity_type="deal",
        entity_id=deal_id,
        instance=deal,
        user=user,
        reason="update",
    )
    recompute_entity_flags(
        db=db,
        entity_type="deal",
        entity_id=deal_id,
        instance=deal,
        user=user,
    )

    return deal


@router.delete("/{deal_id}", responses=NOT_FOUND_RESPONSE)
def delete_deal(
    deal_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin"))],
):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    entity_data = {
        "status": deal.status,
        "price_per_kg": deal.price_per_kg,
        "weight_kg": deal.weight_kg,
    }

    deal.deleted_at = _utcnow()
    db.commit()

    AuditLogger.log_delete(
        db=db,
        user=user,
        entity_type="deal",
        entity_id=deal_id,
        entity_data=entity_data,
    )
    capture_entity_version(
        db=db,
        entity_type="deal",
        entity_id=deal_id,
        instance=deal,
        user=user,
        reason="soft_delete",
    )
    resolve_entity_flags(
        db=db,
        entity_type="deal",
        entity_id=deal_id,
        user=user,
    )

    return {"status": "deleted"}


@router.post(
    "/{deal_id}/restore",
    response_model=DealOut,
    responses=NOT_FOUND_RESPONSE,
)
def restore_deal(
    deal_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin"))],
):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    deal.deleted_at = None
    db.commit()
    db.refresh(deal)

    AuditLogger.log_update(
        db=db,
        user=user,
        entity_type="deal",
        entity_id=deal_id,
        old_data={"deleted_at": "set"},
        new_data={"deleted_at": None},
    )
    capture_entity_version(
        db=db,
        entity_type="deal",
        entity_id=deal_id,
        instance=deal,
        user=user,
        reason="restore",
    )
    recompute_entity_flags(
        db=db,
        entity_type="deal",
        entity_id=deal_id,
        instance=deal,
        user=user,
    )

    return deal
