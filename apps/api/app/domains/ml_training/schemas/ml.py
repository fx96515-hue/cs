"""Schemas for ML routes."""

from pydantic import BaseModel


class TrainModelOut(BaseModel):
    """ML model training result."""

    status: str
    model_id: int
    model_type: str
    algorithm: str
    training_samples: int
    test_samples: int
    metrics: dict[str, float]
    model_path: str


class TrainingStatusOut(BaseModel):
    """ML model status."""

    id: int
    model_name: str
    model_type: str
    model_version: str
    training_date: str
    performance_metrics: dict | None
    training_data_count: int | None
    status: str


class PurchaseTimingOut(BaseModel):
    """Purchase timing recommendation."""

    recommendation: str
    confidence: float
    reason: str
    current_price: float
    average_price: float
    trend: str
    volatility: float
    current_month: int
    details: dict


class ForecastPoint(BaseModel):
    """Single forecast point."""

    date: str
    predicted_price: float
    confidence: float


class PriceForecastOut(BaseModel):
    """Price forecast output."""

    status: str
    forecast_days: int | None = None
    current_price: float | None = None
    forecast: list[ForecastPoint] | None = None
    trend: str | None = None
    note: str | None = None
    message: str | None = None
