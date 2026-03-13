"""Weather and agronomic data for ML features."""

from datetime import date, datetime
from sqlalchemy import String, Float, Integer, Date, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class WeatherAgronomicData(Base, TimestampMixin):
    """
    Advanced weather and agronomic data for ML feature engineering.
    Sources: RAIN4PE, Weatherbit, NASA GPM, SENAMHI
    """

    __tablename__ = "weather_agronomic_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Location
    region: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(64), nullable=False, default="Peru")
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    altitude_m: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Date
    observation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    # Temperature (Celsius)
    temp_min_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    temp_max_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    temp_avg_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Precipitation (mm)
    precipitation_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    precipitation_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Humidity (%)
    humidity_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Agronomic metrics
    soil_moisture_index: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-1
    evapotranspiration_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    solar_radiation_mj: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Risk indicators
    frost_risk: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-1
    drought_stress: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-1
    
    # Source tracking
    source: Mapped[str] = mapped_column(String(64), nullable=False)  # openmeteo, rain4pe, weatherbit, nasa_gpm, senamhi
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    
    # Raw data
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class SocialSentimentData(Base, TimestampMixin):
    """
    Social media sentiment data for market intelligence.
    Sources: Twitter/X, Reddit, Coffee Industry Blogs
    """

    __tablename__ = "social_sentiment_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Source
    platform: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # twitter, reddit, blog
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    author: Mapped[str | None] = mapped_column(String(128), nullable=True)
    
    # Content
    content_text: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    content_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    
    # Timestamps
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Sentiment analysis
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # -1 to 1
    sentiment_magnitude: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0 to 1
    sentiment_label: Mapped[str | None] = mapped_column(String(16), nullable=True)  # positive, negative, neutral
    
    # Topics/Keywords
    topics: Mapped[list | None] = mapped_column(JSON, nullable=True)  # ["price", "quality", "peru"]
    entities: Mapped[list | None] = mapped_column(JSON, nullable=True)  # ["Cooperative X", "Region Y"]
    
    # Engagement
    likes_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comments_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shares_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Market relevance
    market_relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-1
    price_signal: Mapped[str | None] = mapped_column(String(16), nullable=True)  # bullish, bearish, neutral
    
    # Metadata
    language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ShipmentApiEvent(Base, TimestampMixin):
    """
    Real-time shipping events from AIS and port APIs.
    Sources: MarineTraffic, AIS Stream
    """

    __tablename__ = "shipment_api_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Shipment reference
    shipment_id: Mapped[int | None] = mapped_column(ForeignKey("shipments.id"), nullable=True, index=True)
    
    # Vessel info
    vessel_imo: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    vessel_mmsi: Mapped[str | None] = mapped_column(String(16), nullable=True)
    vessel_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    vessel_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vessel_flag: Mapped[str | None] = mapped_column(String(8), nullable=True)
    
    # Position
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed_knots: Mapped[float | None] = mapped_column(Float, nullable=True)
    course: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Event
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # position, port_arrival, port_departure, eta_update
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    # Port info
    port_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    port_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    port_country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # ETA
    eta_destination: Mapped[str | None] = mapped_column(String(128), nullable=True)
    eta_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Source
    source: Mapped[str] = mapped_column(String(32), nullable=False)  # marinetraffic, ais_stream
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class MLFeaturesCache(Base, TimestampMixin):
    """
    Cached ML features for training and inference.
    Pre-computed features from all data sources.
    """

    __tablename__ = "ml_features_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Feature set identifier
    feature_set: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # freight, price, combined
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # Reference (what entity this feature set is for)
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)  # deal, lot, shipment
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    
    # Temporal reference
    feature_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    # Features stored as JSON
    features: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Feature metadata
    feature_names: Mapped[list] = mapped_column(JSON, nullable=False)  # ordered list of feature names
    feature_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Computation info
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    computation_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Data quality
    missing_features: Mapped[list | None] = mapped_column(JSON, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-100


class DataLineageLog(Base, TimestampMixin):
    """
    Audit trail for data provenance and lineage tracking.
    """

    __tablename__ = "data_lineage_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Target record
    table_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Action
    action: Mapped[str] = mapped_column(String(32), nullable=False)  # insert, update, delete, import
    action_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    # Source
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)  # api, csv_import, web_scrape, manual
    source_name: Mapped[str | None] = mapped_column(String(128), nullable=True)  # yahoo_finance, ecb, newsapi
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    
    # User/System
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)  # system, user
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Change details
    old_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Validation
    validation_status: Mapped[str | None] = mapped_column(String(32), nullable=True)  # passed, failed, skipped
    validation_errors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    
    # Metadata
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class SourceHealthMetrics(Base, TimestampMixin):
    """
    Health and performance metrics for each data source.
    For monitoring the 17 data source integrations.
    """

    __tablename__ = "source_health_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Source identification
    source_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_group: Mapped[str] = mapped_column(String(32), nullable=False)  # market, weather, sentiment, logistics, macro, coffee
    
    # Time window
    metric_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    metric_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-23 for hourly metrics
    
    # Request metrics
    requests_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    requests_successful: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    requests_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Latency (ms)
    latency_min_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_max_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_avg_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_p95_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Data metrics
    records_collected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_validated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Error tracking
    error_types: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {"timeout": 5, "rate_limit": 2}
    last_error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    
    # Circuit breaker
    circuit_breaker_status: Mapped[str] = mapped_column(String(16), nullable=False, default="closed")  # closed, open, half_open
    circuit_breaker_trips: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Data quality
    data_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-100
    missing_fields_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    outliers_detected: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Last successful pull
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
