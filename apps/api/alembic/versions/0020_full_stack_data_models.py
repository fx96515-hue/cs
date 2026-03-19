"""Add additive monitoring, sentiment, and feature-cache tables.

Revision ID: 0020_full_stack_data_models
Revises: 0019_milestone1_gap_close
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0020_full_stack_data_models"
down_revision = "0019_milestone1_gap_close"
branch_labels = None
depends_on = None


def _table_exists(inspector: sa.engine.reflection.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _index_exists(
    inspector: sa.engine.reflection.Inspector, table_name: str, index_name: str
) -> bool:
    return any(
        index["name"] == index_name for index in inspector.get_indexes(table_name)
    )


def _create_weather_agronomic_data(
    inspector: sa.engine.reflection.Inspector,
) -> None:
    if _table_exists(inspector, "weather_agronomic_data"):
        return

    op.create_table(
        "weather_agronomic_data",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("region", sa.String(length=128), nullable=False),
        sa.Column(
            "country", sa.String(length=64), nullable=False, server_default="Peru"
        ),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("altitude_m", sa.Integer(), nullable=True),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("temp_min_c", sa.Float(), nullable=True),
        sa.Column("temp_max_c", sa.Float(), nullable=True),
        sa.Column("temp_avg_c", sa.Float(), nullable=True),
        sa.Column("precipitation_mm", sa.Float(), nullable=True),
        sa.Column("precipitation_probability", sa.Float(), nullable=True),
        sa.Column("humidity_min", sa.Float(), nullable=True),
        sa.Column("humidity_max", sa.Float(), nullable=True),
        sa.Column("humidity_avg", sa.Float(), nullable=True),
        sa.Column("soil_moisture_index", sa.Float(), nullable=True),
        sa.Column("evapotranspiration_mm", sa.Float(), nullable=True),
        sa.Column("solar_radiation_mj", sa.Float(), nullable=True),
        sa.Column("wind_speed_kmh", sa.Float(), nullable=True),
        sa.Column("frost_risk", sa.Float(), nullable=True),
        sa.Column("drought_stress", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column(
            "source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=True
        ),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_weather_agronomic_data_region",
        "weather_agronomic_data",
        ["region"],
        unique=False,
    )
    op.create_index(
        "ix_weather_agronomic_data_observation_date",
        "weather_agronomic_data",
        ["observation_date"],
        unique=False,
    )
    op.create_index(
        "ix_weather_agronomic_region_date",
        "weather_agronomic_data",
        ["region", "observation_date"],
        unique=False,
    )


def _create_social_sentiment_data(
    inspector: sa.engine.reflection.Inspector,
) -> None:
    if _table_exists(inspector, "social_sentiment_data"):
        return

    op.create_table(
        "social_sentiment_data",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("author", sa.String(length=128), nullable=True),
        sa.Column("content_text", sa.String(length=4000), nullable=True),
        sa.Column("content_title", sa.String(length=512), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("sentiment_magnitude", sa.Float(), nullable=True),
        sa.Column("sentiment_label", sa.String(length=16), nullable=True),
        sa.Column("topics", sa.JSON(), nullable=True),
        sa.Column("entities", sa.JSON(), nullable=True),
        sa.Column("likes_count", sa.Integer(), nullable=True),
        sa.Column("comments_count", sa.Integer(), nullable=True),
        sa.Column("shares_count", sa.Integer(), nullable=True),
        sa.Column("market_relevance_score", sa.Float(), nullable=True),
        sa.Column("price_signal", sa.String(length=16), nullable=True),
        sa.Column("language", sa.String(length=8), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_social_sentiment_data_platform",
        "social_sentiment_data",
        ["platform"],
        unique=False,
    )
    op.create_index(
        "ix_social_sentiment_data_published_at",
        "social_sentiment_data",
        ["published_at"],
        unique=False,
    )


def _create_shipment_api_events(
    inspector: sa.engine.reflection.Inspector,
) -> None:
    if _table_exists(inspector, "shipment_api_events"):
        return

    op.create_table(
        "shipment_api_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "shipment_id", sa.Integer(), sa.ForeignKey("shipments.id"), nullable=True
        ),
        sa.Column("vessel_imo", sa.String(length=16), nullable=True),
        sa.Column("vessel_mmsi", sa.String(length=16), nullable=True),
        sa.Column("vessel_name", sa.String(length=128), nullable=True),
        sa.Column("vessel_type", sa.String(length=64), nullable=True),
        sa.Column("vessel_flag", sa.String(length=8), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("speed_knots", sa.Float(), nullable=True),
        sa.Column("course", sa.Float(), nullable=True),
        sa.Column("heading", sa.Float(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("port_code", sa.String(length=16), nullable=True),
        sa.Column("port_name", sa.String(length=128), nullable=True),
        sa.Column("port_country", sa.String(length=64), nullable=True),
        sa.Column("eta_destination", sa.String(length=128), nullable=True),
        sa.Column("eta_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_shipment_api_events_shipment_id",
        "shipment_api_events",
        ["shipment_id"],
        unique=False,
    )
    op.create_index(
        "ix_shipment_api_events_vessel_imo",
        "shipment_api_events",
        ["vessel_imo"],
        unique=False,
    )
    op.create_index(
        "ix_shipment_api_events_event_type",
        "shipment_api_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_shipment_api_events_event_time",
        "shipment_api_events",
        ["event_time"],
        unique=False,
    )


def _create_ml_features_cache(inspector: sa.engine.reflection.Inspector) -> None:
    if _table_exists(inspector, "ml_features_cache"):
        return

    op.create_table(
        "ml_features_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("feature_set", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("entity_type", sa.String(length=64), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("feature_date", sa.Date(), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("feature_names", sa.JSON(), nullable=False),
        sa.Column("feature_count", sa.Integer(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("computation_time_ms", sa.Integer(), nullable=True),
        sa.Column("missing_features", sa.JSON(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_ml_features_cache_feature_set",
        "ml_features_cache",
        ["feature_set"],
        unique=False,
    )
    op.create_index(
        "ix_ml_features_cache_entity_id",
        "ml_features_cache",
        ["entity_id"],
        unique=False,
    )
    op.create_index(
        "ix_ml_features_cache_feature_date",
        "ml_features_cache",
        ["feature_date"],
        unique=False,
    )
    op.create_index(
        "ix_ml_features_cache_set_date",
        "ml_features_cache",
        ["feature_set", "feature_date"],
        unique=False,
    )


def _create_data_lineage_log(inspector: sa.engine.reflection.Inspector) -> None:
    if _table_exists(inspector, "data_lineage_log"):
        return

    op.create_table(
        "data_lineage_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("table_name", sa.String(length=128), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("action_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_name", sa.String(length=128), nullable=True),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("old_values", sa.JSON(), nullable=True),
        sa.Column("new_values", sa.JSON(), nullable=True),
        sa.Column("validation_status", sa.String(length=32), nullable=True),
        sa.Column("validation_errors", sa.JSON(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_data_lineage_log_table_name",
        "data_lineage_log",
        ["table_name"],
        unique=False,
    )
    op.create_index(
        "ix_data_lineage_log_record_id",
        "data_lineage_log",
        ["record_id"],
        unique=False,
    )
    op.create_index(
        "ix_data_lineage_log_action_time",
        "data_lineage_log",
        ["action_time"],
        unique=False,
    )


def _create_source_health_metrics(
    inspector: sa.engine.reflection.Inspector,
) -> None:
    if _table_exists(inspector, "source_health_metrics"):
        return

    op.create_table(
        "source_health_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_name", sa.String(length=64), nullable=False),
        sa.Column("source_group", sa.String(length=32), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("metric_hour", sa.Integer(), nullable=True),
        sa.Column("requests_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "requests_successful", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("requests_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_min_ms", sa.Integer(), nullable=True),
        sa.Column("latency_max_ms", sa.Integer(), nullable=True),
        sa.Column("latency_avg_ms", sa.Integer(), nullable=True),
        sa.Column("latency_p95_ms", sa.Integer(), nullable=True),
        sa.Column(
            "records_collected", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "records_validated", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("records_rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_types", sa.JSON(), nullable=True),
        sa.Column("last_error_message", sa.String(length=512), nullable=True),
        sa.Column(
            "circuit_breaker_status",
            sa.String(length=16),
            nullable=False,
            server_default="closed",
        ),
        sa.Column(
            "circuit_breaker_trips", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("data_quality_score", sa.Float(), nullable=True),
        sa.Column("missing_fields_pct", sa.Float(), nullable=True),
        sa.Column("outliers_detected", sa.Integer(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_source_health_metrics_source_name",
        "source_health_metrics",
        ["source_name"],
        unique=False,
    )
    op.create_index(
        "ix_source_health_metrics_metric_date",
        "source_health_metrics",
        ["metric_date"],
        unique=False,
    )
    op.create_index(
        "ix_source_health_metrics_name_date",
        "source_health_metrics",
        ["source_name", "metric_date"],
        unique=False,
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    _create_weather_agronomic_data(inspector)
    _create_social_sentiment_data(inspector)
    _create_shipment_api_events(inspector)
    _create_ml_features_cache(inspector)
    _create_data_lineage_log(inspector)
    _create_source_health_metrics(inspector)


def _drop_index_if_exists(
    inspector: sa.engine.reflection.Inspector, table_name: str, index_name: str
) -> None:
    if _table_exists(inspector, table_name) and _index_exists(
        inspector, table_name, index_name
    ):
        op.drop_index(index_name, table_name=table_name)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    _drop_index_if_exists(
        inspector, "source_health_metrics", "ix_source_health_metrics_name_date"
    )
    _drop_index_if_exists(
        inspector, "source_health_metrics", "ix_source_health_metrics_metric_date"
    )
    _drop_index_if_exists(
        inspector, "source_health_metrics", "ix_source_health_metrics_source_name"
    )
    if _table_exists(inspector, "source_health_metrics"):
        op.drop_table("source_health_metrics")

    _drop_index_if_exists(
        inspector, "data_lineage_log", "ix_data_lineage_log_action_time"
    )
    _drop_index_if_exists(
        inspector, "data_lineage_log", "ix_data_lineage_log_record_id"
    )
    _drop_index_if_exists(
        inspector, "data_lineage_log", "ix_data_lineage_log_table_name"
    )
    if _table_exists(inspector, "data_lineage_log"):
        op.drop_table("data_lineage_log")

    _drop_index_if_exists(
        inspector, "ml_features_cache", "ix_ml_features_cache_set_date"
    )
    _drop_index_if_exists(
        inspector, "ml_features_cache", "ix_ml_features_cache_feature_date"
    )
    _drop_index_if_exists(
        inspector, "ml_features_cache", "ix_ml_features_cache_entity_id"
    )
    _drop_index_if_exists(
        inspector, "ml_features_cache", "ix_ml_features_cache_feature_set"
    )
    if _table_exists(inspector, "ml_features_cache"):
        op.drop_table("ml_features_cache")

    _drop_index_if_exists(
        inspector, "shipment_api_events", "ix_shipment_api_events_event_time"
    )
    _drop_index_if_exists(
        inspector, "shipment_api_events", "ix_shipment_api_events_event_type"
    )
    _drop_index_if_exists(
        inspector, "shipment_api_events", "ix_shipment_api_events_vessel_imo"
    )
    _drop_index_if_exists(
        inspector, "shipment_api_events", "ix_shipment_api_events_shipment_id"
    )
    if _table_exists(inspector, "shipment_api_events"):
        op.drop_table("shipment_api_events")

    _drop_index_if_exists(
        inspector, "social_sentiment_data", "ix_social_sentiment_data_published_at"
    )
    _drop_index_if_exists(
        inspector, "social_sentiment_data", "ix_social_sentiment_data_platform"
    )
    if _table_exists(inspector, "social_sentiment_data"):
        op.drop_table("social_sentiment_data")

    _drop_index_if_exists(
        inspector, "weather_agronomic_data", "ix_weather_agronomic_region_date"
    )
    _drop_index_if_exists(
        inspector,
        "weather_agronomic_data",
        "ix_weather_agronomic_data_observation_date",
    )
    _drop_index_if_exists(
        inspector, "weather_agronomic_data", "ix_weather_agronomic_data_region"
    )
    if _table_exists(inspector, "weather_agronomic_data"):
        op.drop_table("weather_agronomic_data")
