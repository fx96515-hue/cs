from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.transport_event import TransportEvent
from app.schemas.transport_event import TransportEventCreate, TransportEventOut

router = APIRouter()

NOT_FOUND_DETAIL = "Not found"
NOT_FOUND_RESPONSE: dict[int | str, dict[str, Any]] = {
    404: {"description": NOT_FOUND_DETAIL}
}


@router.get("/", response_model=list[TransportEventOut])
def list_transport_events(
    shipment_id: int | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 500,
    *,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    q = db.query(TransportEvent)
    if shipment_id is not None:
        q = q.filter(TransportEvent.shipment_id == shipment_id)
    return q.order_by(TransportEvent.occurred_at.desc()).limit(limit).all()


@router.post("/", response_model=TransportEventOut)
def create_transport_event(
    payload: TransportEventCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
):
    event = TransportEvent(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get(
    "/{event_id}",
    response_model=TransportEventOut,
    responses=NOT_FOUND_RESPONSE,
)
def get_transport_event(
    event_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    event = db.query(TransportEvent).filter(TransportEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return event


@router.delete("/{event_id}", responses=NOT_FOUND_RESPONSE)
def delete_transport_event(
    event_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin"))],
):
    event = db.query(TransportEvent).filter(TransportEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    db.delete(event)
    db.commit()
    return {"status": "deleted"}
