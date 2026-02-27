"""Pydantic schemas for ML predictions."""

from datetime import date
from pydantic import BaseModel, Field


class FreightPredictionRequest(BaseModel):
    """Request schema for freight cost prediction."""

    origin_port: str = Field(..., min_length=1, max_length=255)
    destination_port: str = Field(..., min_length=1, max_length=255)
    weight_kg: int = Field(..., gt=0)
    container_type: str = Field(..., min_length=1)
    departure_date: date


class FreightPrediction(BaseModel):
    """Response schema for freight cost prediction."""

    predicted_cost_usd: float
    confidence_interval_low: float
    confidence_interval_high: float
    confidence_score: float
    factors_considered: list[str]
    similar_historical_shipments: int


class TransitTimeRequest(BaseModel):
    """Request schema for transit time prediction."""

    origin_port: str = Field(..., min_length=1, max_length=255)
    destination_port: str = Field(..., min_length=1, max_length=255)
    departure_date: date


class TransitTimePrediction(BaseModel):
    """Response schema for transit time prediction."""

    predicted_transit_days: int
    min_observed_days: int
    max_observed_days: int
    confidence_score: float
    sample_size: int


class FreightCostTrendRequest(BaseModel):
    """Request schema for freight cost trend."""

    route: str = Field(..., min_length=1)
    months_back: int = Field(default=12, ge=1, le=36)


class TrendDataPoint(BaseModel):
    """Single data point in a trend."""

    month: str
    average_cost: float


class FreightCostTrend(BaseModel):
    """Response schema for freight cost trend."""

    route: str
    trend_data: list[TrendDataPoint]
    average_cost: float
    trend_direction: str


class CoffeePricePredictionRequest(BaseModel):
    """Request schema for coffee price prediction."""

    origin_country: str = Field(..., min_length=1, max_length=255)
    origin_region: str = Field(..., min_length=1, max_length=255)
    variety: str = Field(..., min_length=1, max_length=255)
    process_method: str = Field(..., min_length=1, max_length=255)
    quality_grade: str = Field(..., min_length=1, max_length=255)
    cupping_score: float = Field(..., ge=0, le=100)
    certifications: list[str] = Field(default_factory=list)
    forecast_date: date


class CoffeePricePrediction(BaseModel):
    """Response schema for coffee price prediction."""

    predicted_price_usd_per_kg: float
    confidence_interval_low: float
    confidence_interval_high: float
    confidence_score: float
    market_comparison: str
    price_trend: str


class PriceForecastRequest(BaseModel):
    """Request schema for price forecast."""

    origin_region: str = Field(..., min_length=1, max_length=255)
    months_ahead: int = Field(default=6, ge=1, le=24)


class ForecastDataPoint(BaseModel):
    """Single forecast data point."""

    month: str
    predicted_price: float
    confidence: float


class PriceForecast(BaseModel):
    """Response schema for price forecast."""

    origin_region: str
    forecast_data: list[ForecastDataPoint]
    trend: str


class OptimalPurchaseTimingRequest(BaseModel):
    """Request schema for optimal purchase timing."""

    origin_region: str = Field(..., min_length=1, max_length=255)
    target_price_usd_per_kg: float = Field(..., gt=0)


class OptimalPurchaseTiming(BaseModel):
    """Response schema for optimal purchase timing."""

    origin_region: str
    target_price: float
    recommendation: str
    best_months: list[str]
    forecast_trend: str


class MLModelResponse(BaseModel):
    """Response schema for ML model metadata."""

    id: int
    model_name: str
    model_type: str
    algorithm: str | None = None
    model_version: str
    training_date: str
    performance_metrics: dict
    training_data_count: int
    status: str

    class Config:
        from_attributes = True


class ModelPerformance(BaseModel):
    """Response schema for model performance metrics."""

    mae: float
    rmse: float
    r2_score: float
    accuracy_percentage: float | None = None


class FreightDataImport(BaseModel):
    """Schema for importing freight data."""

    route: str
    origin_port: str
    destination_port: str
    carrier: str
    container_type: str
    weight_kg: int
    freight_cost_usd: float
    transit_days: int
    departure_date: date
    arrival_date: date
    season: str
    fuel_price_index: float | None = None
    port_congestion_score: float | None = None


class PriceDataImport(BaseModel):
    """Schema for importing price data."""

    date: date
    origin_country: str
    origin_region: str
    variety: str
    process_method: str
    quality_grade: str
    cupping_score: float | None = None
    certifications: list[str] | None = None
    price_usd_per_kg: float
    price_usd_per_lb: float
    ice_c_price_usd_per_lb: float
    differential_usd_per_lb: float
    market_source: str


class DataImportResponse(BaseModel):
    """Response schema for data import."""

    status: str
    records_imported: int
    message: str | None = None
