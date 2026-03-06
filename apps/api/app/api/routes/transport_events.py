from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.transport_event import TransportEvent
from app.schemas.transport_event import TransportEventCreate, TransportEventOut

router = APIRouter()


@router.get("/", response_model=list[TransportEventOut])
def list_transport_events(
    shipment_id: int | None = None,
    limit: int = Query(500, ge=1, le=1000),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    q = db.query(TransportEvent)
    if shipment_id is not None:
        q = q.filter(TransportEvent.shipment_id == shipment_id)
    return q.order_by(TransportEvent.occurred_at.desc()).limit(limit).all()


@router.post("/", response_model=TransportEventOut)
def create_transport_event(
    payload: TransportEventCreate,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    event = TransportEvent(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/{event_id}", response_model=TransportEventOut)
def get_transport_event(
    event_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    event = db.query(TransportEvent).filter(TransportEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Not found")
    return event


@router.delete("/{event_id}")
def delete_transport_event(
    event_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    event = db.query(TransportEvent).filter(TransportEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(event)
    db.commit()
    return {"status": "deleted"}
