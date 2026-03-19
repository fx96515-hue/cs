import os
from typing import Tuple

from sqlalchemy import func

from app.db.session import SessionLocal
from app.models.cooperative import Cooperative
from app.models.region import Region
from app.models.peru_region import PeruRegion


DEFAULT_COUNTRY = os.getenv("DEFAULT_REGION_COUNTRY", "Peru")


def _parse_region(value: str) -> Tuple[str, str]:
    parts = [p.strip() for p in value.split(",") if p.strip()]
    if len(parts) >= 2:
        return parts[0], parts[1]
    return value.strip(), DEFAULT_COUNTRY


def _find_or_create_region(db, name: str, country: str) -> Region:
    region = (
        db.query(Region)
        .filter(
            func.lower(Region.name) == name.lower(),
            func.lower(Region.country) == country.lower(),
        )
        .first()
    )
    if region:
        return region

    peru_match = (
        db.query(PeruRegion).filter(func.lower(PeruRegion.name) == name.lower()).first()
    )
    if peru_match and country.lower() == "peru":
        name = peru_match.name

    region = Region(name=name, country=country)
    db.add(region)
    db.commit()
    db.refresh(region)
    return region


def main() -> None:
    db = SessionLocal()
    try:
        coops = (
            db.query(Cooperative)
            .filter(Cooperative.region_id.is_(None), Cooperative.region.isnot(None))
            .all()
        )
        updated = 0
        for coop in coops:
            if not coop.region or not coop.region.strip():
                continue
            region_name, country = _parse_region(coop.region)
            region = _find_or_create_region(db, region_name, country)
            coop.region_id = region.id
            updated += 1
        db.commit()
        print(f"Updated cooperatives with region_id: {updated}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
