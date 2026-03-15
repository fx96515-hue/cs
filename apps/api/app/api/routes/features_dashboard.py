from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.coffee_price_history import CoffeePriceHistory
from app.models.freight_history import FreightHistory
from app.models.ml_model import MLModel
from app.services.ml.advanced_features import FeatureEngineer
from app.services.ml.bulk_importer import BulkImportManager
from app.services.ml.data_collection import DataCollectionService
from app.services.ml.data_quality import QualityReport
from app.services.ml.model_management import MLModelManagementService

router = APIRouter()


def _safe_validation_summary(validation: dict[str, Any]) -> dict[str, Any]:
    return {
        "validRows": int(validation.get("valid_rows", 0) or 0),
        "invalidRows": int(validation.get("invalid_rows", 0) or 0),
        "totalRows": int(validation.get("total_rows", 0) or 0),
        "errorCount": len(validation.get("errors") or []),
    }


def _feature_category(name: str) -> str:
    lowered = name.lower()
    if any(token in lowered for token in ("fuel", "port", "carrier", "route", "container", "transit", "freight")):
        return "Fracht-Features"
    if any(token in lowered for token in ("price", "ice", "differential", "cupping", "quality", "cert", "origin", "process")):
        return "Preis-Features"
    return "Cross-Features"


def _feature_description(name: str) -> str:
    return name.replace("_", " ").strip().capitalize()


def _catalog_payload() -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for category, feature_names in FeatureEngineer.feature_catalog().items():
        payload.append(
            {
                "name": category,
                "features": [
                    {
                        "name": feature_name,
                        "description": _feature_description(feature_name),
                        "type": "numeric",
                        "importance": 0.0,
                        "coverage": 0.0,
                        "lastComputed": datetime.utcnow().isoformat(),
                    }
                    for feature_name in feature_names
                ],
            }
        )
    return payload


def _load_feature_importance(model: MLModel) -> dict[str, float]:
    model_path = Path(model.model_file_path)
    if not model_path.exists():
        return {}

    try:
        if model.model_type in {"freight_cost", "freight_prediction"}:
            if model.algorithm == "xgboost":
                from app.ml.xgboost_freight_model import XGBoostFreightCostModel

                ml_model: Any = XGBoostFreightCostModel()
            else:
                from app.ml.freight_model import FreightCostModel

                ml_model = FreightCostModel()
        else:
            if model.algorithm == "xgboost":
                from app.ml.xgboost_price_model import XGBoostCoffeePriceModel

                ml_model = XGBoostCoffeePriceModel()
            else:
                from app.ml.price_model import CoffeePriceModel

                ml_model = CoffeePriceModel()

        ml_model.load(str(model_path))
        return ml_model.get_feature_importance()
    except Exception:
        return {}


@router.get("/importance")
def features_importance(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    stmt = (
        select(MLModel)
        .where(MLModel.status == "active")
        .order_by(MLModel.training_date.desc())
    )
    models = list(db.execute(stmt).scalars().all())

    grouped: dict[str, list[dict[str, Any]]] = {
        "Fracht-Features": [],
        "Preis-Features": [],
        "Cross-Features": [],
    }

    for model in models:
        importances = _load_feature_importance(model)
        raw_features: Any = model.features_used
        if isinstance(raw_features, list):
            fallback_features = [str(feature) for feature in raw_features]
        elif isinstance(raw_features, dict):
            fallback_features = [str(feature) for feature in raw_features.keys()]
        else:
            fallback_features = []

        if not importances and fallback_features:
            equal_weight = round(1 / max(len(fallback_features), 1), 4)
            importances = {feature: equal_weight for feature in fallback_features}

        for feature_name, importance in importances.items():
            category = _feature_category(feature_name)
            grouped[category].append(
                {
                    "name": feature_name,
                    "description": _feature_description(feature_name),
                    "type": "numeric",
                    "importance": float(importance),
                    "coverage": 100.0 if model.training_data_count > 0 else 0.0,
                    "lastComputed": model.training_date.isoformat(),
                }
            )

    payload: list[dict[str, Any]] = []
    for category, features in grouped.items():
        if not features:
            continue
        payload.append(
            {
                "name": category,
                "features": sorted(
                    features,
                    key=lambda item: float(item.get("importance", 0.0)),
                    reverse=True,
                ),
            }
        )
    return payload or _catalog_payload()


@router.get("/catalog")
def features_catalog(
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    return _catalog_payload()


@router.get("/quality-report")
def features_quality_report(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    model_count = db.execute(select(func.count()).select_from(MLModel)).scalar_one()
    freight_count = db.execute(select(func.count()).select_from(FreightHistory)).scalar_one()
    price_count = db.execute(select(func.count()).select_from(CoffeePriceHistory)).scalar_one()

    latest_training = db.execute(select(func.max(MLModel.training_date))).scalar_one()
    total_features = 0
    for model in db.execute(select(MLModel.features_used)).all():
        raw: Any = model[0]
        if isinstance(raw, list):
            total_features += len(raw)
        elif isinstance(raw, dict):
            total_features += len(raw.keys())

    freight_rows = list(
        db.execute(
            select(
                FreightHistory.freight_cost_usd,
                FreightHistory.transit_days,
            )
        ).all()
    )
    price_rows = list(
        db.execute(
            select(
                CoffeePriceHistory.price_usd_per_kg,
                CoffeePriceHistory.price_usd_per_lb,
            )
        ).all()
    )
    total_records = int(freight_count or 0) + int(price_count or 0)
    freight_quality = QualityReport.generate_report(
        [
            {
                "delay_hours": max((transit_days or 0) * 24 - 24, 0),
                "speed_knots": 20,
            }
            for _, transit_days in freight_rows
        ],
        "freight",
    )
    price_quality = QualityReport.generate_report(
        [{"price": price_usd_per_lb or price_usd_per_kg} for price_usd_per_kg, price_usd_per_lb in price_rows],
        "price",
    )
    avg_quality_score = round(
        ((freight_quality["quality_score"] + price_quality["quality_score"]) / 2) * 100,
        2,
    )
    missing_data_points = max(total_records * max(total_features, 1) - total_features, 0)
    catalog_feature_count = sum(len(item["features"]) for item in _catalog_payload())
    return {
        "totalFeatures": total_features or catalog_feature_count,
        "avgCoverage": avg_quality_score if total_records > 0 else 0.0,
        "avgImportance": round(1 / max(total_features, 1), 4) if total_features else 0.0,
        "missingDataPoints": missing_data_points,
        "lastUpdate": latest_training.isoformat() if latest_training else datetime.utcnow().isoformat(),
        "modelsTracked": int(model_count or 0),
        "trainingRecords": total_records,
        "catalogFeatures": catalog_feature_count,
        "qualityLabel": (
            "excellent"
            if avg_quality_score >= 90
            else "good"
            if avg_quality_score >= 75
            else "fair"
            if avg_quality_score >= 50
            else "poor"
        ),
        "anomaliesDetected": int(freight_quality["anomaly_count"]) + int(price_quality["anomaly_count"]),
    }


@router.post("/compute-all")
async def features_compute_all(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin"))],
):
    service = MLModelManagementService(db)
    freight = await service.trigger_model_retraining("freight_cost")
    coffee = await service.trigger_model_retraining("coffee_price")
    return {"status": "processed", "jobs": [freight, coffee]}


def _parse_csv_records(content: str) -> list[dict[str, str]]:
    reader = csv.DictReader(StringIO(content))
    return [
        {str(key).strip(): (value or "").strip() for key, value in row.items()}
        for row in reader
        if any((value or "").strip() for value in row.values())
    ]


@router.post("/bulk-import")
async def features_bulk_import(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin"))],
    file: UploadFile = File(...),
):
    content = (await file.read()).decode("utf-8-sig")
    rows = _parse_csv_records(content)
    if not rows:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    service = DataCollectionService(db)
    headers = {header.lower() for header in rows[0].keys()}

    if "freight_cost_usd" in headers:
        validation = BulkImportManager.import_data(content, "freight")
        if validation["valid_rows"] == 0:
            raise HTTPException(status_code=400, detail=validation["errors"] or ["CSV validation failed"])
        payload = []
        for row in rows:
            payload.append(
                {
                    "route": row["route"],
                    "origin_port": row["origin_port"],
                    "destination_port": row["destination_port"],
                    "carrier": row["carrier"],
                    "container_type": row["container_type"],
                    "weight_kg": int(row["weight_kg"]),
                    "freight_cost_usd": float(row["freight_cost_usd"]),
                    "transit_days": int(row["transit_days"]),
                    "departure_date": row["departure_date"],
                    "arrival_date": row["arrival_date"],
                    "season": row["season"],
                    "fuel_price_index": float(row["fuel_price_index"]) if row.get("fuel_price_index") else None,
                    "port_congestion_score": float(row["port_congestion_score"]) if row.get("port_congestion_score") else None,
                }
            )
        imported = await service.import_freight_data(payload)
        return {
            "status": "success",
            "recordsImported": int(imported or 0),
            "dataset": "freight",
            "validation": _safe_validation_summary(validation),
        }

    if "price_usd_per_kg" in headers:
        validation = BulkImportManager.import_data(content, "price")
        if validation["valid_rows"] == 0:
            raise HTTPException(status_code=400, detail=validation["errors"] or ["CSV validation failed"])
        payload = []
        for row in rows:
            payload.append(
                {
                    "date": row["date"],
                    "origin_country": row["origin_country"],
                    "origin_region": row["origin_region"],
                    "variety": row["variety"],
                    "process_method": row["process_method"],
                    "quality_grade": row["quality_grade"],
                    "cupping_score": float(row["cupping_score"]) if row.get("cupping_score") else None,
                    "certifications": [part.strip() for part in row.get("certifications", "").split(",") if part.strip()],
                    "price_usd_per_kg": float(row["price_usd_per_kg"]),
                    "price_usd_per_lb": float(row["price_usd_per_lb"]),
                    "ice_c_price_usd_per_lb": float(row["ice_c_price_usd_per_lb"]),
                    "differential_usd_per_lb": float(row["differential_usd_per_lb"]),
                    "market_source": row["market_source"],
                }
            )
        imported = await service.import_price_data(payload)
        return {
            "status": "success",
            "recordsImported": int(imported or 0),
            "dataset": "price",
            "validation": _safe_validation_summary(validation),
        }

    raise HTTPException(
        status_code=400,
        detail="CSV headers do not match supported freight or price import formats",
    )


@router.get("/import-template/{data_type}")
def features_import_template(
    data_type: str,
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    templates: dict[str, dict[str, Any]] = {
        "price": {
            "columns": [
                "date",
                "origin_country",
                "origin_region",
                "variety",
                "process_method",
                "quality_grade",
                "cupping_score",
                "certifications",
                "price_usd_per_kg",
                "price_usd_per_lb",
                "ice_c_price_usd_per_lb",
                "differential_usd_per_lb",
                "market_source",
            ],
            "description": "Historische Kaffeepreise fuer Modelltraining und Qualitaetspruefung.",
        },
        "freight": {
            "columns": [
                "route",
                "origin_port",
                "destination_port",
                "carrier",
                "container_type",
                "weight_kg",
                "freight_cost_usd",
                "transit_days",
                "departure_date",
                "arrival_date",
                "season",
                "fuel_price_index",
                "port_congestion_score",
            ],
            "description": "Historische Frachtdaten fuer Kosten- und Transitmodelle.",
        },
        "weather": {
            "columns": [
                "region",
                "observation_date",
                "temp_min_c",
                "temp_max_c",
                "precipitation_mm",
                "source",
            ],
            "description": "Wetter- und Agrarsignale fuer spaetere Feature-Erweiterungen.",
        },
    }
    if data_type not in templates:
        raise HTTPException(status_code=404, detail=f"Unknown template: {data_type}")
    return {"dataType": data_type, **templates[data_type]}
