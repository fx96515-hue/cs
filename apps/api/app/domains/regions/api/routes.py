from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.peru_region import PeruRegion
from app.models.region import Region
from app.domains.regions.schemas.regions import PeruRegionOut, RegionOut
from app.domains.regions.services.peru_seed import seed_default_regions


router = APIRouter()


@router.get("/", response_model=list[RegionOut])
def list_regions(
    country: Annotated[
        str | None,
        Query(min_length=2, max_length=64, pattern=r"^[A-Za-z][A-Za-z\s-]*$"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=2000)] = 500,
    *,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    q = db.query(Region)
    if country:
        normalized_country = " ".join(country.split())
        q = q.filter(Region.country == normalized_country)
    if hasattr(Region, "deleted_at"):
        q = q.filter(Region.deleted_at.is_(None))
    return q.order_by(Region.country.asc(), Region.name.asc()).limit(limit).all()


@router.get("/peru", response_model=list[PeruRegionOut])
def list_peru_regions(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    return db.query(PeruRegion).order_by(PeruRegion.name.asc()).all()


@router.post("/peru/seed")
def seed(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
):
    return seed_default_regions(db)
