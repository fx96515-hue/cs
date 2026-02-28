"""Add cooperative intelligence fields and regions table

Revision ID: 0016_add_cooperative_fields_and_regions
Revises: 0015_add_ml_model_algorithm
Create Date: 2026-02-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0016_add_cooperative_fields_and_regions"
down_revision = "0015_add_ml_model_algorithm"
branch_labels = None
depends_on = None


def _column_exists(inspector: sa.engine.reflection.Inspector, table: str, column: str) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "cooperatives" in inspector.get_table_names():
        coop_columns = [
            "operational_data",
            "export_readiness",
            "financial_data",
            "social_impact_data",
            "digital_footprint",
            "sourcing_scores",
            "communication_metrics",
        ]
        for col_name in coop_columns:
            if not _column_exists(inspector, "cooperatives", col_name):
                op.add_column(
                    "cooperatives",
                    sa.Column(col_name, sa.JSON(), nullable=True),
                )

    if "regions" not in inspector.get_table_names():
        op.create_table(
            "regions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("country", sa.String(length=64), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("elevation_min_m", sa.Float(), nullable=True),
            sa.Column("elevation_max_m", sa.Float(), nullable=True),
            sa.Column("avg_temperature_c", sa.Float(), nullable=True),
            sa.Column("rainfall_mm", sa.Float(), nullable=True),
            sa.Column("humidity_pct", sa.Float(), nullable=True),
            sa.Column("soil_type", sa.String(length=128), nullable=True),
            sa.Column("production_volume_kg", sa.Float(), nullable=True),
            sa.Column("production_share_pct", sa.Float(), nullable=True),
            sa.Column("harvest_months", sa.String(length=64), nullable=True),
            sa.Column("typical_varieties", sa.String(length=255), nullable=True),
            sa.Column("typical_processing", sa.String(length=128), nullable=True),
            sa.Column("quality_profile", sa.Text(), nullable=True),
            sa.Column("main_port", sa.String(length=64), nullable=True),
            sa.Column("transport_time_hours", sa.Float(), nullable=True),
            sa.Column("logistics_cost_per_kg", sa.Float(), nullable=True),
            sa.Column("infrastructure_score", sa.Float(), nullable=True),
            sa.Column("weather_risk", sa.String(length=32), nullable=True),
            sa.Column("political_risk", sa.String(length=32), nullable=True),
            sa.Column("logistics_risk", sa.String(length=32), nullable=True),
            sa.Column("quality_consistency_score", sa.Float(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.UniqueConstraint("name", "country", name="uq_region_name_country"),
        )
        op.create_index("ix_regions_name", "regions", ["name"], unique=False)
        op.create_index("ix_regions_country", "regions", ["country"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "regions" in inspector.get_table_names():
        op.drop_index("ix_regions_country", table_name="regions")
        op.drop_index("ix_regions_name", table_name="regions")
        op.drop_table("regions")

    if "cooperatives" in inspector.get_table_names():
        coop_columns = {
            col["name"] for col in inspector.get_columns("cooperatives")
        }
        for col_name in [
            "communication_metrics",
            "sourcing_scores",
            "digital_footprint",
            "social_impact_data",
            "financial_data",
            "export_readiness",
            "operational_data",
        ]:
            if col_name in coop_columns:
                op.drop_column("cooperatives", col_name)
