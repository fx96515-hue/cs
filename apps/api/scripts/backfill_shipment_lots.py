from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.shipment import Shipment
from app.models.shipment_lot import ShipmentLot


def _exists(db: Session, shipment_id: int, lot_id: int) -> bool:
    return (
        db.query(ShipmentLot)
        .filter(
            ShipmentLot.shipment_id == shipment_id,
            ShipmentLot.lot_id == lot_id,
        )
        .first()
        is not None
    )


def main() -> None:
    db = SessionLocal()
    try:
        shipments = db.query(Shipment).filter(Shipment.lot_id.isnot(None)).all()
        created = 0
        for shipment in shipments:
            lot_id = shipment.lot_id
            if lot_id is None:
                continue
            if _exists(db, shipment.id, lot_id):
                continue
            db.add(ShipmentLot(shipment_id=shipment.id, lot_id=lot_id))
            created += 1
        db.commit()
        print(f"Created shipment_lots rows: {created}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
