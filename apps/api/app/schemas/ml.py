"""Compatibility wrapper for ML schemas.

Canonical implementation lives in app.domains.ml_training.schemas.ml.
"""

from app.domains.ml_training.schemas.ml import (
    ForecastPoint,
    PriceForecastOut,
    PurchaseTimingOut,
    TrainModelOut,
    TrainingStatusOut,
)

__all__ = [
    "TrainModelOut",
    "TrainingStatusOut",
    "PurchaseTimingOut",
    "ForecastPoint",
    "PriceForecastOut",
]
