from datetime import datetime, timezone
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.api.response_utils import apply_create_status
from app.core.idempotency import find_existing_by_fields
from app.db.session import get_db
from app.models.shipment import Shipment
from app.models.shipment_lot import ShipmentLot
from app.models.transport_event import TransportEvent
from app.models.user import User
from app.domains.shipments.schemas.shipment import (
    ShipmentCreate,
    ShipmentOut,
    ShipmentUpdate,
    TrackingEventCreate,
)
from app.core.audit import AuditLogger
from app.core.versioning import capture_entity_version
from app.domains.data_quality.services.flags import recompute_entity_flags, resolve_entity_flags

router = APIRouter()
ShipmentStatusFilter = Literal[
    "in_transit", "arrived", "customs", "delivered", "delayed", "pending", "archived"
]

SHIPMENT_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"description": "Invalid request"},
    404: {"description": "Shipment not found"},
    422: {"description": "Invalid datetime format"},
}
NOT_FOUND_DETAIL = "Not found"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _utcnow_iso() -> str:
    return _utcnow().isoformat()


def _parse_iso_datetime_or_422(value: str, field_name: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid ISO-8601 datetime for '{field_name}'",
        ) from exc


def _ensure_unique_identifiers(db: Session, payload: ShipmentCreate) -> None:
    checks = (
        ("container_number", payload.container_number, "Container number already exists"),
        ("bill_of_lading", payload.bill_of_lading, "Bill of lading already exists"),
    )
    for column_name, value, error_message in checks:
        existing = (
            db.query(Shipment)
            .filter(
                getattr(Shipment, column_name) == value,
                Shipment.deleted_at.is_(None),
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail=error_message)


def _apply_create_datetime_fields(shipment: Shipment, payload: ShipmentCreate) -> None:
    if payload.departure_at and not payload.departure_date:
        shipment.departure_date = payload.departure_at.isoformat()
    if payload.estimated_arrival_at and not payload.estimated_arrival:
        shipment.estimated_arrival = payload.estimated_arrival_at.isoformat()
    if payload.actual_arrival_at and not payload.actual_arrival:
        shipment.actual_arrival = payload.actual_arrival_at.isoformat()

    if payload.departure_at is None and payload.departure_date:
        shipment.departure_at = _parse_iso_datetime_or_422(
            payload.departure_date, "departure_date"
        )
    if payload.estimated_arrival_at is None and payload.estimated_arrival:
        shipment.estimated_arrival_at = _parse_iso_datetime_or_422(
            payload.estimated_arrival, "estimated_arrival"
        )
    if payload.actual_arrival_at is None and payload.actual_arrival:
        shipment.actual_arrival_at = _parse_iso_datetime_or_422(
            payload.actual_arrival, "actual_arrival"
        )


def _dedupe_lot_ids(lot_ids: list[int] | None) -> list[int]:
    if not lot_ids:
        return []
    return list(dict.fromkeys(lot_ids))


def _resolve_create_lot_ids(payload: ShipmentCreate, shipment: Shipment) -> list[int]:
    if payload.lot_ids:
        lot_ids = _dedupe_lot_ids(payload.lot_ids)
        if shipment.lot_id is None and lot_ids:
            shipment.lot_id = lot_ids[0]
        return lot_ids
    if payload.lot_id:
        return [payload.lot_id]
    return []


def _apply_update_datetime_fields(update_dict: dict[str, Any], current_status: str) -> None:
    if "departure_at" in update_dict and update_dict.get("departure_at"):
        update_dict.setdefault("departure_date", update_dict["departure_at"].isoformat())
    if "estimated_arrival_at" in update_dict and update_dict.get("estimated_arrival_at"):
        update_dict.setdefault(
            "estimated_arrival", update_dict["estimated_arrival_at"].isoformat()
        )
    if "actual_arrival_at" in update_dict and update_dict.get("actual_arrival_at"):
        update_dict.setdefault("actual_arrival", update_dict["actual_arrival_at"].isoformat())

    if "departure_at" not in update_dict and "departure_date" in update_dict:
        update_dict["departure_at"] = _parse_iso_datetime_or_422(
            update_dict["departure_date"], "departure_date"
        )
    if "estimated_arrival_at" not in update_dict and "estimated_arrival" in update_dict:
        update_dict["estimated_arrival_at"] = _parse_iso_datetime_or_422(
            update_dict["estimated_arrival"], "estimated_arrival"
        )
    if "actual_arrival_at" not in update_dict and "actual_arrival" in update_dict:
        update_dict["actual_arrival_at"] = _parse_iso_datetime_or_422(
            update_dict["actual_arrival"], "actual_arrival"
        )

    if "status" in update_dict and update_dict["status"] != current_status:
        update_dict["status_updated_at"] = _utcnow_iso()


def _build_shipment_out(db: Session, shipment: Shipment) -> ShipmentOut:
    lot_ids = [
        row.lot_id
        for row in db.query(ShipmentLot)
        .filter(ShipmentLot.shipment_id == shipment.id)
        .all()
    ]
    base = ShipmentOut.model_validate(shipment)
    return base.model_copy(update={"lot_ids": lot_ids})


def _build_shipment_list_out(
    db: Session, shipments: list[Shipment]
) -> list[ShipmentOut]:
    if not shipments:
        return []
    shipment_ids = [s.id for s in shipments]
    lot_map: dict[int, list[int]] = {sid: [] for sid in shipment_ids}
    rows = db.query(ShipmentLot).filter(ShipmentLot.shipment_id.in_(shipment_ids)).all()
    for row in rows:
        lot_map.setdefault(row.shipment_id, []).append(row.lot_id)
    result: list[ShipmentOut] = []
    for shipment in shipments:
        base = ShipmentOut.model_validate(shipment)
        result.append(base.model_copy(update={"lot_ids": lot_map.get(shipment.id, [])}))
    return result


@router.get("/", response_model=list[ShipmentOut])
def list_shipments(
    status: ShipmentStatusFilter | None = None,
    origin_port: str | None = None,
    destination_port: str | None = None,
    include_deleted: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    *,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    """List all shipments with optional filters."""
    q = db.query(Shipment)
    if not include_deleted:
        q = q.filter(Shipment.deleted_at.is_(None))
    if status:
        q = q.filter(Shipment.status == status)
    if origin_port:
        q = q.filter(Shipment.origin_port == origin_port)
    if destination_port:
        q = q.filter(Shipment.destination_port == destination_port)
    shipments = q.order_by(Shipment.created_at.desc()).limit(limit).all()
    return _build_shipment_list_out(db, shipments)


@router.get("/active", response_model=list[ShipmentOut])
def list_active_shipments(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    """Get active shipments (status=in_transit)."""
    shipments = (
        db.query(Shipment)
        .filter(Shipment.status == "in_transit", Shipment.deleted_at.is_(None))
        .order_by(Shipment.created_at.desc())
        .all()
    )
    return _build_shipment_list_out(db, shipments)


@router.get("/delayed", response_model=list[ShipmentOut])
def list_delayed_shipments(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    """Get delayed shipments (delay_hours > 0)."""
    shipments = (
        db.query(Shipment)
        .filter(Shipment.delay_hours > 0, Shipment.deleted_at.is_(None))
        .order_by(Shipment.delay_hours.desc())
        .all()
    )
    return _build_shipment_list_out(db, shipments)


@router.post(
    "/",
    response_model=ShipmentOut,
    status_code=201,
    responses=SHIPMENT_ERROR_RESPONSES,
)
def create_shipment(
    payload: ShipmentCreate,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin", "analyst"))],
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
    _ensure_unique_identifiers(db, payload)

    shipment = Shipment(**payload.model_dump(exclude={"lot_ids"}))
    _apply_create_datetime_fields(shipment, payload)
    lot_ids = _resolve_create_lot_ids(payload, shipment)
    shipment.tracking_events = []  # Initialize empty tracking events
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    for lot_id in lot_ids:
        db.add(ShipmentLot(shipment_id=shipment.id, lot_id=lot_id))
    if lot_ids:
        db.commit()

    # Log creation for audit trail
    AuditLogger.log_create(
        db=db,
        user=user,
        entity_type="shipment",
        entity_id=shipment.id,
        entity_data=payload.model_dump(),
    )
    capture_entity_version(
        db=db,
        entity_type="shipment",
        entity_id=shipment.id,
        instance=shipment,
        user=user,
        reason="create",
    )
    recompute_entity_flags(
        db=db,
        entity_type="shipment",
        entity_id=shipment.id,
        instance=shipment,
        user=user,
    )

    apply_create_status(request, response, created=True)

    return _build_shipment_out(db, shipment)


@router.get(
    "/{shipment_id}",
    response_model=ShipmentOut,
    responses=SHIPMENT_ERROR_RESPONSES,
)
def get_shipment(
    shipment_id: Annotated[int, Path(ge=1)],
    include_deleted: Annotated[bool, Query()] = False,
    *,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    """Get shipment details."""
    q = db.query(Shipment).filter(Shipment.id == shipment_id)
    if not include_deleted:
        q = q.filter(Shipment.deleted_at.is_(None))
    shipment = q.first()
    if not shipment:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return _build_shipment_out(db, shipment)


@router.patch(
    "/{shipment_id}",
    response_model=ShipmentOut,
    responses=SHIPMENT_ERROR_RESPONSES,
)
def update_shipment(
    shipment_id: Annotated[int, Path(ge=1)],
    payload: ShipmentUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin", "analyst"))],
):
    """Update shipment."""
    shipment = (
        db.query(Shipment)
        .filter(Shipment.id == shipment_id, Shipment.deleted_at.is_(None))
        .first()
    )
    if not shipment:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    # Capture old data for audit log
    old_data = {
        k: getattr(shipment, k) for k in payload.model_dump(exclude_unset=True).keys()
    }

    # Update status_updated_at if status is changing
    update_dict = payload.model_dump(exclude_unset=True, exclude={"lot_ids"})
    _apply_update_datetime_fields(update_dict, shipment.status)

    for k, v in update_dict.items():
        setattr(shipment, k, v)
    db.commit()
    db.refresh(shipment)

    if payload.lot_ids is not None:
        db.query(ShipmentLot).filter(ShipmentLot.shipment_id == shipment_id).delete()
        for lot_id in _dedupe_lot_ids(payload.lot_ids):
            db.add(ShipmentLot(shipment_id=shipment_id, lot_id=lot_id))
        shipment.lot_id = payload.lot_ids[0] if payload.lot_ids else None
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
    capture_entity_version(
        db=db,
        entity_type="shipment",
        entity_id=shipment_id,
        instance=shipment,
        user=user,
        reason="update",
    )
    recompute_entity_flags(
        db=db,
        entity_type="shipment",
        entity_id=shipment_id,
        instance=shipment,
        user=user,
    )

    return _build_shipment_out(db, shipment)


@router.delete("/{shipment_id}", responses=SHIPMENT_ERROR_RESPONSES)
def delete_shipment(
    shipment_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin"))],
):
    """Delete shipment."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    # Capture data before deletion for audit log
    entity_data = {
        "container_number": shipment.container_number,
        "origin_port": shipment.origin_port,
        "destination_port": shipment.destination_port,
    }

    shipment.deleted_at = _utcnow()
    db.commit()

    # Log deletion for audit trail
    AuditLogger.log_delete(
        db=db,
        user=user,
        entity_type="shipment",
        entity_id=shipment_id,
        entity_data=entity_data,
    )
    capture_entity_version(
        db=db,
        entity_type="shipment",
        entity_id=shipment_id,
        instance=shipment,
        user=user,
        reason="soft_delete",
    )
    resolve_entity_flags(
        db=db,
        entity_type="shipment",
        entity_id=shipment_id,
        user=user,
    )

    return {"status": "deleted"}


@router.post(
    "/{shipment_id}/restore",
    response_model=ShipmentOut,
    responses=SHIPMENT_ERROR_RESPONSES,
)
def restore_shipment(
    shipment_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin"))],
):
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    shipment.deleted_at = None
    db.commit()
    db.refresh(shipment)

    AuditLogger.log_update(
        db=db,
        user=user,
        entity_type="shipment",
        entity_id=shipment_id,
        old_data={"deleted_at": "set"},
        new_data={"deleted_at": None},
    )
    capture_entity_version(
        db=db,
        entity_type="shipment",
        entity_id=shipment_id,
        instance=shipment,
        user=user,
        reason="restore",
    )
    recompute_entity_flags(
        db=db,
        entity_type="shipment",
        entity_id=shipment_id,
        instance=shipment,
        user=user,
    )

    return _build_shipment_out(db, shipment)


@router.post(
    "/{shipment_id}/track",
    response_model=ShipmentOut,
    responses=SHIPMENT_ERROR_RESPONSES,
)
def add_tracking_event(
    shipment_id: Annotated[int, Path(ge=1)],
    event: TrackingEventCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin", "analyst"))],
):
    """Add a tracking event to a shipment."""
    shipment = (
        db.query(Shipment)
        .filter(Shipment.id == shipment_id, Shipment.deleted_at.is_(None))
        .first()
    )
    if not shipment:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

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
    shipment.tracking_events = tracking_events.copy()

    # Update current location
    shipment.current_location = event.location

    # Mark the field as modified to ensure SQLAlchemy commits the change
    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(shipment, "tracking_events")

    db.commit()
    db.refresh(shipment)

    occurred_at = _parse_iso_datetime_or_422(event.timestamp, "timestamp")
    db.add(
        TransportEvent(
            shipment_id=shipment_id,
            event_type=event.event,
            location=event.location,
            occurred_at=occurred_at,
            status=shipment.status,
            details={"details": event.details} if event.details else None,
        )
    )
    db.commit()

    # Log tracking event for audit trail
    AuditLogger.log_update(
        db=db,
        user=user,
        entity_type="shipment",
        entity_id=shipment_id,
        old_data={"tracking_event_count": len(tracking_events) - 1},
        new_data={"tracking_event": new_event},
    )
    capture_entity_version(
        db=db,
        entity_type="shipment",
        entity_id=shipment_id,
        instance=shipment,
        user=user,
        reason="tracking_event",
    )
    recompute_entity_flags(
        db=db,
        entity_type="shipment",
        entity_id=shipment_id,
        instance=shipment,
        user=user,
    )

    return _build_shipment_out(db, shipment)
