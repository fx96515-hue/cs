from app.db.session import SessionLocal
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster
from app.models.lot import Lot
from app.models.shipment import Shipment
from app.services.data_quality import recompute_entity_flags


def _recompute_for_all(db, model, entity_type: str) -> int:
    rows = (
        db.query(model)
        .filter(getattr(model, "deleted_at").is_(None))
        .all()
    )
    count = 0
    for row in rows:
        recompute_entity_flags(
            db=db,
            entity_type=entity_type,
            entity_id=row.id,
            instance=row,
            user=None,
        )
        count += 1
    return count


def main() -> None:
    db = SessionLocal()
    try:
        total = 0
        total += _recompute_for_all(db, Cooperative, "cooperative")
        total += _recompute_for_all(db, Roaster, "roaster")
        total += _recompute_for_all(db, Lot, "lot")
        total += _recompute_for_all(db, Shipment, "shipment")
        print(f"Recomputed data quality for entities: {total}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
