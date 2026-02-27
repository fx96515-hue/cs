"""Add ML prediction tables

Revision ID: 0009_ml_prediction_tables
Revises: 0008_timestamp_defaults_kb_cupping_v0_3_2b
Create Date: 2025-12-29
"""

from alembic import op
import sqlalchemy as sa

revision = "0009_ml_prediction_tables"
down_revision = "0008_timestamp_defaults_kb_cupping_v0_3_2b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create freight_history table
    op.create_table(
        "freight_history",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("route", sa.String(255), nullable=False),
        sa.Column("origin_port", sa.String(255), nullable=False),
        sa.Column("destination_port", sa.String(255), nullable=False),
        sa.Column("carrier", sa.String(255), nullable=False),
        sa.Column("container_type", sa.String(16), nullable=False),
        sa.Column("weight_kg", sa.Integer, nullable=False),
        sa.Column("freight_cost_usd", sa.Float, nullable=False),
        sa.Column("transit_days", sa.Integer, nullable=False),
        sa.Column("departure_date", sa.Date, nullable=False),
        sa.Column("arrival_date", sa.Date, nullable=False),
        sa.Column("season", sa.String(8), nullable=False),
        sa.Column("fuel_price_index", sa.Float, nullable=True),
        sa.Column("port_congestion_score", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_freight_history_route", "freight_history", ["route"])

    # Create coffee_price_history table
    op.create_table(
        "coffee_price_history",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("origin_country", sa.String(255), nullable=False),
        sa.Column("origin_region", sa.String(255), nullable=False),
        sa.Column("variety", sa.String(255), nullable=False),
        sa.Column("process_method", sa.String(255), nullable=False),
        sa.Column("quality_grade", sa.String(255), nullable=False),
        sa.Column("cupping_score", sa.Float, nullable=True),
        sa.Column("certifications", sa.JSON, nullable=True),
        sa.Column("price_usd_per_kg", sa.Float, nullable=False),
        sa.Column("price_usd_per_lb", sa.Float, nullable=False),
        sa.Column("ice_c_price_usd_per_lb", sa.Float, nullable=False),
        sa.Column("differential_usd_per_lb", sa.Float, nullable=False),
        sa.Column("market_source", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_coffee_price_history_date", "coffee_price_history", ["date"])
    op.create_index(
        "ix_coffee_price_history_country", "coffee_price_history", ["origin_country"]
    )

    # Create ml_models table
    op.create_table(
        "ml_models",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("model_type", sa.String(64), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("training_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("features_used", sa.JSON, nullable=False),
        sa.Column("performance_metrics", sa.JSON, nullable=False),
        sa.Column("training_data_count", sa.Integer, nullable=False),
        sa.Column("model_file_path", sa.String(512), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_ml_models_type", "ml_models", ["model_type"])
    op.create_index("ix_ml_models_status", "ml_models", ["status"])


def downgrade() -> None:
    op.drop_index("ix_ml_models_status", "ml_models")
    op.drop_index("ix_ml_models_type", "ml_models")
    op.drop_table("ml_models")

    op.drop_index("ix_coffee_price_history_country", "coffee_price_history")
    op.drop_index("ix_coffee_price_history_date", "coffee_price_history")
    op.drop_table("coffee_price_history")

    op.drop_index("ix_freight_history_route", "freight_history")
    op.drop_table("freight_history")
