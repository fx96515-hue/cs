from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.schemas.logistics import LandedCostRequest, LandedCostResponse
from app.services.logistics import calc_landed_cost


router = APIRouter()


@router.post("/landed-cost", response_model=LandedCostResponse)
def landed_cost(
    payload: LandedCostRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    return calc_landed_cost(db, **payload.model_dump())
