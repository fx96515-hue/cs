"""ML training pipeline for freight and coffee price models."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sqlalchemy.orm import Session

from app.ml.model_factory import (
    algorithm_for_model,
    create_freight_model,
    create_price_model,
)
from app.models.freight_history import FreightHistory
from app.models.coffee_price_history import CoffeePriceHistory
from app.models.ml_model import MLModel


def _latest_sentiment_for_region(db: Session, region: str | None) -> float:
    """Return the most recent sentiment score for a region, or 0.0 if unavailable."""
    try:
        from app.models.sentiment_score import SentimentScore

        row = (
            db.query(SentimentScore.score)
            .filter(SentimentScore.region == (region or "global"))
            .order_by(SentimentScore.scored_at.desc())
            .first()
        )
        return float(row[0]) if row else 0.0
    except Exception:
        return 0.0


def collect_freight_training_data(db: Session) -> pd.DataFrame:
    """Collect historical freight data for training.

    Args:
        db: Database session

    Returns:
        DataFrame with freight training data
    """
    records = db.query(FreightHistory).all()

    if not records:
        raise ValueError("No freight history data available for training")

    data = []
    for record in records:
        data.append(
            {
                "route": record.route,
                "container_type": record.container_type,
                "weight_kg": record.weight_kg,
                "season": record.season or "unknown",
                "carrier": record.carrier or "unknown",
                "fuel_price_index": record.fuel_price_index or 100.0,
                "port_congestion_score": record.port_congestion_score or 50.0,
                "freight_cost_usd": record.freight_cost_usd,
            }
        )

    return pd.DataFrame(data)


def collect_price_training_data(db: Session) -> pd.DataFrame:
    """Collect historical coffee price data for training.

    Args:
        db: Database session

    Returns:
        DataFrame with price training data
    """
    records = db.query(CoffeePriceHistory).all()

    if not records:
        raise ValueError("No coffee price history data available for training")

    data = []
    for record in records:
        # Parse certifications if stored as JSON/string
        cert_list: list[str] = []
        if hasattr(record, "certifications") and record.certifications:
            # Certifications typed as dict | None, but handle legacy list/str data
            cert_value = cast(Any, record.certifications)
            if isinstance(cert_value, list):
                cert_list = cert_value
            elif isinstance(cert_value, str):
                cert_list = [c.strip() for c in cert_value.split(",")]

        data.append(
            {
                "origin_country": record.origin_country or "Peru",
                "origin_region": record.origin_region or "unknown",
                "variety": record.variety or "unknown",
                "process_method": record.process_method or "washed",
                "quality_grade": record.quality_grade or "specialty",
                "market_source": record.market_source or "direct",
                "cupping_score": record.cupping_score or 82.0,
                "certifications": cert_list,
                "ice_c_price_usd_per_lb": record.ice_c_price_usd_per_lb or 2.0,
                "date": record.date,
                "price_usd_per_kg": record.price_usd_per_kg,
                "sentiment_score": _latest_sentiment_for_region(
                    db, record.origin_region
                ),
            }
        )

    return pd.DataFrame(data)


def train_freight_model(
    db: Session, *, test_size: float = 0.2, random_state: int = 42
) -> dict[str, Any]:
    """Train the freight cost model.

    Args:
        db: Database session
        test_size: Proportion of data for testing
        random_state: Random seed

    Returns:
        Training results with metrics
    """
    # Collect data
    data = collect_freight_training_data(db)

    # Initialize model
    model = create_freight_model()
    algorithm = algorithm_for_model(model)

    # Prepare features
    X, y = model.prepare_features(data)

    if X is None or y is None:
        raise ValueError("Failed to prepare features")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Train
    model.train(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Save model
    model_dir = Path("models")
    model_dir.mkdir(exist_ok=True)
    model_path = (
        model_dir / f"freight_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
    )
    model.save(str(model_path))

    # Save metadata to DB
    ml_model = MLModel(
        model_name="freight_cost_predictor",
        model_type="freight_cost",
        model_version=datetime.now().strftime("%Y%m%d_%H%M%S"),
        training_date=datetime.now(timezone.utc),
        features_used=[
            "route",
            "container_type",
            "weight_kg",
            "season",
            "fuel_price_index",
            "port_congestion_score",
        ],
        performance_metrics={"rmse": float(rmse), "mae": float(mae), "r2": float(r2)},
        training_data_count=len(data),
        model_file_path=str(model_path),
        status="active",
        algorithm=algorithm,
    )
    db.add(ml_model)
    db.commit()
    db.refresh(ml_model)

    return {
        "status": "success",
        "model_id": ml_model.id,
        "model_type": "freight_cost",
        "algorithm": algorithm,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "metrics": {"rmse": float(rmse), "mae": float(mae), "r2": float(r2)},
        "model_path": str(model_path),
    }


def train_price_model(
    db: Session, *, test_size: float = 0.2, random_state: int = 42
) -> dict[str, Any]:
    """Train the coffee price model.

    Args:
        db: Database session
        test_size: Proportion of data for testing
        random_state: Random seed

    Returns:
        Training results with metrics
    """
    # Collect data
    data = collect_price_training_data(db)

    # Initialize model
    model = create_price_model()
    algorithm = algorithm_for_model(model)

    # Prepare features
    X, y = model.prepare_features(data)

    if X is None or y is None:
        raise ValueError("Failed to prepare features")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Train
    model.train(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Save model
    model_dir = Path("models")
    model_dir.mkdir(exist_ok=True)
    model_path = (
        model_dir / f"price_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
    )
    model.save(str(model_path))

    # Save metadata to DB
    ml_model = MLModel(
        model_name="coffee_price_predictor",
        model_type="coffee_price",
        model_version=datetime.now().strftime("%Y%m%d_%H%M%S"),
        training_date=datetime.now(timezone.utc),
        features_used=[
            "origin_country",
            "origin_region",
            "variety",
            "process_method",
            "quality_grade",
            "cupping_score",
            "certifications",
            "ice_c_price",
        ],
        performance_metrics={"rmse": float(rmse), "mae": float(mae), "r2": float(r2)},
        training_data_count=len(data),
        model_file_path=str(model_path),
        status="active",
        algorithm=algorithm,
    )
    db.add(ml_model)
    db.commit()
    db.refresh(ml_model)

    return {
        "status": "success",
        "model_id": ml_model.id,
        "model_type": "coffee_price",
        "algorithm": algorithm,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "metrics": {"rmse": float(rmse), "mae": float(mae), "r2": float(r2)},
        "model_path": str(model_path),
    }


def should_retrain(db: Session, model_type: str, *, min_new_data: int = 100) -> bool:
    """Check if model should be retrained.

    Args:
        db: Database session
        model_type: Type of model ('freight_cost' or 'coffee_price')
        min_new_data: Minimum new records needed to trigger retraining

    Returns:
        True if retraining is recommended
    """
    # Get latest model
    latest_model = (
        db.query(MLModel)
        .filter(MLModel.model_type == model_type)
        .order_by(MLModel.training_date.desc())
        .first()
    )

    if not latest_model:
        return True  # No model exists

    # Count new data since last training
    if model_type == "freight_cost":
        new_count = (
            db.query(FreightHistory)
            .filter(FreightHistory.created_at > latest_model.training_date)
            .count()
        )
    else:
        new_count = (
            db.query(CoffeePriceHistory)
            .filter(CoffeePriceHistory.created_at > latest_model.training_date)
            .count()
        )

    return new_count >= min_new_data
