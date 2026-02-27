from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.peru_region import PeruRegion
from app.schemas.regions import PeruRegionOut
from app.services.peru_regions import seed_default_regions


router = APIRouter()


@router.get("/peru", response_model=list[PeruRegionOut])
def list_peru_regions(
    db: Session = Depends(get_db), _=Depends(require_role("admin", "analyst", "viewer"))
):
    return db.query(PeruRegion).order_by(PeruRegion.name.asc()).all()


@router.post("/peru/seed")
def seed(db: Session = Depends(get_db), _=Depends(require_role("admin", "analyst"))):
    return seed_default_regions(db)
