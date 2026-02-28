"""API routes for ML predictions."""

from fastapi import APIRouter, Depends, HTTPException
from celery.result import AsyncResult
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.schemas.ml_predictions import (
    FreightPredictionRequest,
    FreightPrediction,
    TransitTimeRequest,
    TransitTimePrediction,
    FreightCostTrend,
    CoffeePricePredictionRequest,
    CoffeePricePrediction,
    PriceForecastRequest,
    PriceForecast,
    OptimalPurchaseTimingRequest,
    OptimalPurchaseTiming,
    MLModelResponse,
    FreightDataImport,
    PriceDataImport,
    DataImportResponse,
    BatchFreightPredictionRequest,
    BatchFreightPredictionResponse,
    BatchCoffeePricePredictionRequest,
    BatchCoffeePricePredictionResponse,
    AsyncTaskResponse,
    AsyncTaskStatus,
)
from app.services.ml.freight_prediction import FreightPredictionService
from app.services.ml.price_prediction import CoffeePricePredictionService
from app.services.ml.model_management import MLModelManagementService
from app.services.ml.data_collection import DataCollectionService
from app.workers.celery_app import celery

router = APIRouter()


@router.post("/predict-freight", response_model=FreightPrediction)
async def predict_freight_cost(
    request: FreightPredictionRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Predict freight cost for a shipment."""
    service = FreightPredictionService(db)
    result = await service.predict_freight_cost(
        origin_port=request.origin_port,
        destination_port=request.destination_port,
        weight_kg=request.weight_kg,
        container_type=request.container_type,
        departure_date=request.departure_date,
    )
    return result


@router.post("/predict-freight/batch", response_model=BatchFreightPredictionResponse)
async def predict_freight_batch(
    request: BatchFreightPredictionRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Batch predict freight costs."""
    service = FreightPredictionService(db)
    results: list[FreightPrediction | None] = []
    errors: list[dict] = []

    for idx, item in enumerate(request.requests):
        try:
            result = await service.predict_freight_cost(
                origin_port=item.origin_port,
                destination_port=item.destination_port,
                weight_kg=item.weight_kg,
                container_type=item.container_type,
                departure_date=item.departure_date,
            )
            results.append(result)  # type: ignore[arg-type]
        except Exception as exc:
            results.append(None)
            errors.append({"index": idx, "error": str(exc)})

    return BatchFreightPredictionResponse(results=results, errors=errors)


@router.post("/predict-freight/batch/async", response_model=AsyncTaskResponse)
async def predict_freight_batch_async(
    request: BatchFreightPredictionRequest,
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Enqueue freight batch prediction."""
    payload = [item.model_dump(mode="json") for item in request.requests]
    task = celery.send_task("app.workers.tasks.predict_freight_batch", args=[payload])
    return AsyncTaskResponse(status="queued", task_id=task.id)


@router.post("/predict-transit-time", response_model=TransitTimePrediction)
async def predict_transit_time(
    request: TransitTimeRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Predict transit time for a route."""
    service = FreightPredictionService(db)
    result = await service.predict_transit_time(
        origin_port=request.origin_port,
        destination_port=request.destination_port,
        departure_date=request.departure_date,
    )
    return result


@router.get("/freight-cost-trend", response_model=FreightCostTrend)
async def get_freight_cost_trend(
    route: str,
    months_back: int = 12,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Get historical freight cost trend for a route."""
    service = FreightPredictionService(db)
    result = await service.get_cost_trend(route=route, months_back=months_back)
    return result


@router.post("/predict-coffee-price", response_model=CoffeePricePrediction)
async def predict_coffee_price(
    request: CoffeePricePredictionRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Predict coffee price based on attributes."""
    service = CoffeePricePredictionService(db)
    result = await service.predict_coffee_price(
        origin_country=request.origin_country,
        origin_region=request.origin_region,
        variety=request.variety,
        process_method=request.process_method,
        quality_grade=request.quality_grade,
        cupping_score=request.cupping_score,
        certifications=request.certifications,
        forecast_date=request.forecast_date,
    )
    return result


@router.post(
    "/predict-coffee-price/batch", response_model=BatchCoffeePricePredictionResponse
)
async def predict_coffee_price_batch(
    request: BatchCoffeePricePredictionRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Batch predict coffee prices."""
    service = CoffeePricePredictionService(db)
    results: list[CoffeePricePrediction | None] = []
    errors: list[dict] = []

    for idx, item in enumerate(request.requests):
        try:
            result = await service.predict_coffee_price(
                origin_country=item.origin_country,
                origin_region=item.origin_region,
                variety=item.variety,
                process_method=item.process_method,
                quality_grade=item.quality_grade,
                cupping_score=item.cupping_score,
                certifications=item.certifications,
                forecast_date=item.forecast_date,
            )
            results.append(result)  # type: ignore[arg-type]
        except Exception as exc:
            results.append(None)
            errors.append({"index": idx, "error": str(exc)})

    return BatchCoffeePricePredictionResponse(results=results, errors=errors)


@router.post("/predict-coffee-price/batch/async", response_model=AsyncTaskResponse)
async def predict_coffee_price_batch_async(
    request: BatchCoffeePricePredictionRequest,
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Enqueue coffee price batch prediction."""
    payload = [item.model_dump(mode="json") for item in request.requests]
    task = celery.send_task(
        "app.workers.tasks.predict_coffee_price_batch", args=[payload]
    )
    return AsyncTaskResponse(status="queued", task_id=task.id)


@router.post("/forecast-price-trend", response_model=PriceForecast)
async def forecast_price_trend(
    request: PriceForecastRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Forecast price trend for a region."""
    service = CoffeePricePredictionService(db)
    result = await service.forecast_price_trend(
        origin_region=request.origin_region, months_ahead=request.months_ahead
    )
    return result


@router.post("/optimal-purchase-timing", response_model=OptimalPurchaseTiming)
async def calculate_optimal_purchase_timing(
    request: OptimalPurchaseTimingRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Calculate optimal purchase timing based on price forecasts."""
    service = CoffeePricePredictionService(db)
    result = await service.calculate_optimal_purchase_timing(
        origin_region=request.origin_region,
        target_price_usd_per_kg=request.target_price_usd_per_kg,
    )
    return result


@router.get("/tasks/{task_id}", response_model=AsyncTaskStatus)
async def ml_task_status(
    task_id: str, _=Depends(require_role("admin", "analyst", "viewer"))
):
    """Check async ML task status."""
    res = AsyncResult(task_id, app=celery)
    payload = None
    try:
        payload = res.result if res.ready() else None
    except Exception:
        payload = None
    return AsyncTaskStatus(
        task_id=task_id, state=res.state, ready=res.ready(), result=payload
    )


@router.get("/models/{model_id}/feature-importance", response_model=dict)
async def get_feature_importance(
    model_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    """Get feature importances for a specific trained model.

    Returns a mapping of feature name to normalised importance score (0–1).
    Only available for models that support feature importance (XGBoost and
    Random Forest).
    """
    import logging
    import os
    from pathlib import Path

    from app.models.ml_model import MLModel
    from sqlalchemy import select as sa_select

    logger = logging.getLogger(__name__)

    stmt = sa_select(MLModel).where(MLModel.id == model_id)
    result = db.execute(stmt)
    model_meta = result.scalar_one_or_none()

    if not model_meta:
        raise HTTPException(status_code=404, detail="Model not found")

    if not model_meta.model_file_path or not os.path.exists(model_meta.model_file_path):
        raise HTTPException(
            status_code=404,
            detail="Model file not found on disk. Please retrain the model.",
        )

    # Security: resolve the path and ensure it is inside the expected models/ dir.
    try:
        resolved = Path(model_meta.model_file_path).resolve()
        models_dir = Path("models").resolve()
        resolved.relative_to(models_dir)  # raises ValueError if outside
    except ValueError:
        safe_model_key = str(model_id).replace("\r", "").replace("\n", "")
        logger.warning(
            "Feature importance requested for model_id=%s with suspicious path: %s",
            safe_model_key,
            model_meta.model_file_path,
        )
        raise HTTPException(
            status_code=400, detail="Model file path is not in the expected directory."
        )

    # Determine whether this is a freight or price model type.
    _FREIGHT_TYPES = {"freight_cost", "freight_prediction"}
    _PRICE_TYPES = {"coffee_price", "price_prediction"}
    model_type_key = model_meta.model_type
    if model_type_key not in _FREIGHT_TYPES | _PRICE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Feature importance not supported for model_type '{model_type_key}'.",
        )

    algorithm = model_meta.algorithm or "random_forest"

    try:
        if model_type_key in _FREIGHT_TYPES:
            if algorithm == "xgboost":
                from app.ml.xgboost_freight_model import XGBoostFreightCostModel

                m: object = XGBoostFreightCostModel()
            else:
                from app.ml.freight_model import FreightCostModel

                m = FreightCostModel()
        else:
            if algorithm == "xgboost":
                from app.ml.xgboost_price_model import XGBoostCoffeePriceModel

                m = XGBoostCoffeePriceModel()
            else:
                from app.ml.price_model import CoffeePriceModel

                m = CoffeePriceModel()

        m.load(str(resolved))  # type: ignore[attr-defined]
        importances = m.get_feature_importance()  # type: ignore[attr-defined]
    except Exception:
        safe_model_id_int = int(model_id)
        logger.exception(
            "Failed to compute feature importance for model_id=%d",
            safe_model_id_int,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to compute feature importance. Check server logs for details.",
        )

    return {
        "model_id": model_id,
        "model_type": model_meta.model_type,
        "algorithm": algorithm,
        "feature_importance": importances,
    }


@router.get("/models", response_model=list[MLModelResponse])
async def list_ml_models(
    model_type: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    """List all ML models with optional type filter."""
    service = MLModelManagementService(db)
    models = await service.list_models(model_type=model_type)
    return models


@router.get("/models/{model_id}", response_model=dict)
async def get_model_details(
    model_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    """Get detailed information about a specific model."""
    service = MLModelManagementService(db)
    model = await service.get_model_performance(model_id)

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return model


@router.post("/models/{model_id}/retrain", response_model=dict)
async def retrain_model(
    model_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    """Trigger retraining for a specific model."""
    service = MLModelManagementService(db)

    # Get model to find its type
    model = await service.get_model_performance(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    result = await service.trigger_model_retraining(model["model_type"])
    return result


@router.post("/data/import-freight", response_model=DataImportResponse)
async def import_freight_data(
    data: list[FreightDataImport],
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    """Import historical freight data for ML training."""
    service = DataCollectionService(db)

    # Convert Pydantic models to dicts
    data_dicts = [record.model_dump() for record in data]

    try:
        count = await service.import_freight_data(data_dicts)
        return DataImportResponse(
            status="success",
            records_imported=count,
            message=f"Successfully imported {count} freight records",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")


@router.post("/data/import-prices", response_model=DataImportResponse)
async def import_price_data(
    data: list[PriceDataImport],
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    """Import historical coffee price data for ML training."""
    service = DataCollectionService(db)

    # Convert Pydantic models to dicts
    data_dicts = [record.model_dump() for record in data]

    try:
        count = await service.import_price_data(data_dicts)
        return DataImportResponse(
            status="success",
            records_imported=count,
            message=f"Successfully imported {count} price records",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")
