"""Additional monitoring and agronomic models adapted from PR721."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class WeatherAgronomicData(Base, TimestampMixin):
    __tablename__ = "weather_agronomic_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    region: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(64), nullable=False, default="Peru")
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    altitude_m: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    temp_min_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    temp_max_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    temp_avg_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    precipitation_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    precipitation_probability: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    humidity_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    soil_moisture_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    evapotranspiration_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    solar_radiation_mj: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    frost_risk: Mapped[float | None] = mapped_column(Float, nullable=True)
    drought_stress: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("sources.id"), nullable=True
    )
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class SocialSentimentData(Base, TimestampMixin):
    __tablename__ = "social_sentiment_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    author: Mapped[str | None] = mapped_column(String(128), nullable=True)
    content_text: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    content_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_magnitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_label: Mapped[str | None] = mapped_column(String(16), nullable=True)
    topics: Mapped[list | None] = mapped_column(JSON, nullable=True)
    entities: Mapped[list | None] = mapped_column(JSON, nullable=True)
    likes_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comments_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shares_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    market_relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_signal: Mapped[str | None] = mapped_column(String(16), nullable=True)
    language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ShipmentApiEvent(Base, TimestampMixin):
    __tablename__ = "shipment_api_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    shipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("shipments.id"), nullable=True, index=True
    )
    vessel_imo: Mapped[str | None] = mapped_column(
        String(16), nullable=True, index=True
    )
    vessel_mmsi: Mapped[str | None] = mapped_column(String(16), nullable=True)
    vessel_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    vessel_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vessel_flag: Mapped[str | None] = mapped_column(String(8), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed_knots: Mapped[float | None] = mapped_column(Float, nullable=True)
    course: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    port_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    port_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    port_country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    eta_destination: Mapped[str | None] = mapped_column(String(128), nullable=True)
    eta_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class MLFeaturesCache(Base, TimestampMixin):
    __tablename__ = "ml_features_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    feature_set: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    feature_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    features: Mapped[dict] = mapped_column(JSON, nullable=False)
    feature_names: Mapped[list] = mapped_column(JSON, nullable=False)
    feature_count: Mapped[int] = mapped_column(Integer, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    computation_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    missing_features: Mapped[list | None] = mapped_column(JSON, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)


class DataLineageLog(Base, TimestampMixin):
    __tablename__ = "data_lineage_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    table_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    action_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    old_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    validation_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    validation_errors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class SourceHealthMetrics(Base, TimestampMixin):
    __tablename__ = "source_health_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_group: Mapped[str] = mapped_column(String(32), nullable=False)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    metric_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    requests_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    requests_successful: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    requests_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_min_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_max_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_avg_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_p95_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    records_collected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_validated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_types: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    circuit_breaker_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="closed"
    )
    circuit_breaker_trips: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    data_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    missing_fields_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    outliers_detected: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_failure_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
