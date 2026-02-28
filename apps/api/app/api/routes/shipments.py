from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.deps import require_role
from app.api.response_utils import apply_create_status
from app.core.idempotency import find_existing_by_fields
from app.db.session import get_db
from app.models.shipment import Shipment
from app.models.user import User
from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentOut,
    ShipmentUpdate,
    TrackingEventCreate,
)
from app.core.audit import AuditLogger

router = APIRouter()


@router.get("/", response_model=list[ShipmentOut])
def list_shipments(
    status: str | None = None,
    origin_port: str | None = None,
    destination_port: str | None = None,
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """List all shipments with optional filters."""
    q = db.query(Shipment)
    if status:
        q = q.filter(Shipment.status == status)
    if origin_port:
        q = q.filter(Shipment.origin_port == origin_port)
    if destination_port:
        q = q.filter(Shipment.destination_port == destination_port)
    return q.order_by(Shipment.created_at.desc()).limit(limit).all()


@router.get("/active", response_model=list[ShipmentOut])
def list_active_shipments(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Get active shipments (status=in_transit)."""
    return (
        db.query(Shipment)
        .filter(Shipment.status == "in_transit")
        .order_by(Shipment.created_at.desc())
        .all()
    )


@router.get("/delayed", response_model=list[ShipmentOut])
def list_delayed_shipments(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Get delayed shipments (delay_hours > 0)."""
    return (
        db.query(Shipment)
        .filter(Shipment.delay_hours > 0)
        .order_by(Shipment.delay_hours.desc())
        .all()
    )


@router.post("/", response_model=ShipmentOut, status_code=201)
def create_shipment(
    payload: ShipmentCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "analyst")),
):
    """Create a new shipment."""
    # Idempotent create: return existing shipment if both identifiers match.
    existing = find_existing_by_fields(
        db,
        Shipment,
        {
            "container_number": payload.container_number,
            "bill_of_lading": payload.bill_of_lading,
        },
    )
    if existing:
        apply_create_status(request, response, created=False)
        return existing

    # Otherwise, enforce uniqueness constraints.
    existing_container = (
        db.query(Shipment)
        .filter(Shipment.container_number == payload.container_number)
        .first()
    )
    if existing_container:
        raise HTTPException(status_code=400, detail="Container number already exists")

    existing_bol = (
        db.query(Shipment)
        .filter(Shipment.bill_of_lading == payload.bill_of_lading)
        .first()
    )
    if existing_bol:
        raise HTTPException(status_code=400, detail="Bill of lading already exists")

    shipment = Shipment(**payload.model_dump())
    shipment.tracking_events = []  # Initialize empty tracking events
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    # Log creation for audit trail
    AuditLogger.log_create(
        db=db,
        user=user,
        entity_type="shipment",
        entity_id=shipment.id,
        entity_data=payload.model_dump(),
    )

    apply_create_status(request, response, created=True)

    return shipment


@router.get("/{shipment_id}", response_model=ShipmentOut)
def get_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Get shipment details."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Not found")
    return shipment


@router.patch("/{shipment_id}", response_model=ShipmentOut)
def update_shipment(
    shipment_id: int,
    payload: ShipmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "analyst")),
):
    """Update shipment."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Not found")

    # Capture old data for audit log
    old_data = {
        k: getattr(shipment, k) for k in payload.model_dump(exclude_unset=True).keys()
    }

    # Update status_updated_at if status is changing
    update_dict = payload.model_dump(exclude_unset=True)
    if "status" in update_dict and update_dict["status"] != shipment.status:
        update_dict["status_updated_at"] = datetime.now().isoformat()

    for k, v in update_dict.items():
        setattr(shipment, k, v)
    db.commit()
    db.refresh(shipment)

    # Log update for audit trail
    AuditLogger.log_update(
        db=db,
        user=user,
        entity_type="shipment",
        entity_id=shipment_id,
        old_data=old_data,
        new_data=payload.model_dump(exclude_unset=True),
    )

    return shipment


@router.delete("/{shipment_id}")
def delete_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Delete shipment."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Not found")

    # Capture data before deletion for audit log
    entity_data = {
        "container_number": shipment.container_number,
        "origin_port": shipment.origin_port,
        "destination_port": shipment.destination_port,
    }

    db.delete(shipment)
    db.commit()

    # Log deletion for audit trail
    AuditLogger.log_delete(
        db=db,
        user=user,
        entity_type="shipment",
        entity_id=shipment_id,
        entity_data=entity_data,
    )

    return {"status": "deleted"}


@router.post("/{shipment_id}/track", response_model=ShipmentOut)
def add_tracking_event(
    shipment_id: int,
    event: TrackingEventCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "analyst")),
):
    """Add a tracking event to a shipment."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Not found")

    # Get existing tracking events or initialize
    # Defensive handling in case of unexpected data format
    raw_events = shipment.tracking_events
    if isinstance(raw_events, list):
        tracking_events: list[dict] = raw_events
    else:
        tracking_events = []

    # Add new event
    new_event = event.model_dump()
    tracking_events.append(new_event)

    # Force SQLAlchemy to detect the change by creating a new list
    shipment.tracking_events = list(tracking_events)

    # Update current location
    shipment.current_location = event.location

    # Mark the field as modified to ensure SQLAlchemy commits the change
    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(shipment, "tracking_events")

    db.commit()
    db.refresh(shipment)

    # Log tracking event for audit trail
    AuditLogger.log_update(
        db=db,
        user=user,
        entity_type="shipment",
        entity_id=shipment_id,
        old_data={"tracking_event_count": len(tracking_events) - 1},
        new_data={"tracking_event": new_event},
    )

    return shipment
