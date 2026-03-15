"""Add quality_alerts table

Revision ID: 0012_add_quality_alerts_table
Revises: 0011_add_shipments_table
Create Date: 2026-02-11

"""

from alembic import op
import sqlalchemy as sa


revision = "0012_add_quality_alerts_table"
down_revision = "0011_add_shipments_table"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "quality_alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(length=32), nullable=False, index=True),
        sa.Column("entity_id", sa.Integer(), nullable=False, index=True),
        sa.Column("alert_type", sa.String(length=64), nullable=False, index=True),
        sa.Column("field_name", sa.String(length=64), nullable=True),
        sa.Column("old_value", sa.Float(), nullable=True),
        sa.Column("new_value", sa.Float(), nullable=True),
        sa.Column("change_amount", sa.Float(), nullable=True),
        sa.Column(
            "severity",
            sa.String(length=16),
            nullable=False,
            server_default="info",
            index=True,
        ),
        sa.Column(
            "acknowledged",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            index=True,
        ),
        sa.Column("acknowledged_by", sa.String(length=255), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
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
    )

    # Create composite indexes
    op.create_index(
        "ix_quality_alerts_entity_type_id",
        "quality_alerts",
        ["entity_type", "entity_id"],
        unique=False,
    )
    op.create_index(
        "ix_quality_alerts_severity_ack",
        "quality_alerts",
        ["severity", "acknowledged"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_quality_alerts_severity_ack", table_name="quality_alerts")
    op.drop_index("ix_quality_alerts_entity_type_id", table_name="quality_alerts")
    op.drop_table("quality_alerts")
