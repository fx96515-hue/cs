"""ML model training and prediction routes."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role, get_db
from app.domains.ml_training.schemas.ml import (
    TrainModelOut,
    TrainingStatusOut,
    PurchaseTimingOut,
    PriceForecastOut,
)
from app.services.ml.training_pipeline import train_freight_model, train_price_model
from app.services.ml.purchase_timing import (
    get_purchase_timing_recommendation,
    get_price_forecast,
)
from app.services.ml.model_management import MLModelManagementService


router = APIRouter()
MLTrainingModelType = Literal["freight_cost", "coffee_price"]


@router.post(
    "/train/{model_type}",
    response_model=TrainModelOut,
    responses={
        400: {"description": "Invalid training request"},
        500: {"description": "Training failed"},
    },
)
def train_model(
    model_type: MLTrainingModelType,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin"))],
):
    """Trigger model training.

    model_type: 'freight_cost' or 'coffee_price'
    """
    try:
        if model_type == "freight_cost":
            result = train_freight_model(db)
        else:
            result = train_price_model(db)
        return result
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid training request")
    except Exception:
        raise HTTPException(status_code=500, detail="Training failed")


@router.get("/training-status", response_model=list[TrainingStatusOut])
async def get_training_status(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
    model_type: Annotated[MLTrainingModelType | None, Query()] = None,
):
    """Get training pipeline status."""
    service = MLModelManagementService(db)
    models = await service.list_models(model_type=model_type)
    return models


@router.get("/optimal-purchase-timing", response_model=PurchaseTimingOut)
def optimal_purchase_timing(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
    origin_region: str | None = None,
    target_quantity_kg: float | None = None,
):
    """Get optimal purchase timing recommendation."""
    result = get_purchase_timing_recommendation(
        db, origin_region=origin_region, target_quantity_kg=target_quantity_kg
    )
    return result


@router.get("/price-forecast", response_model=PriceForecastOut)
def price_forecast(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
    origin_region: str | None = None,
    days: Annotated[int, Query(ge=1, le=90)] = 30,
):
    """Get price forecast for next N days."""
    result = get_price_forecast(db, origin_region=origin_region, days_ahead=days)
    return result
