"""Add shipments table

Revision ID: 0011_add_shipments_table
Revises: 0010_seed_ml_data
Create Date: 2025-12-30

"""

from alembic import op
import sqlalchemy as sa


revision = "0011_add_shipments_table"
down_revision = "0010_seed_ml_data"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "shipments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "lot_id", sa.Integer(), sa.ForeignKey("lots.id"), nullable=True, index=True
        ),
        sa.Column(
            "cooperative_id",
            sa.Integer(),
            sa.ForeignKey("cooperatives.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "roaster_id",
            sa.Integer(),
            sa.ForeignKey("roasters.id"),
            nullable=True,
            index=True,
        ),
        # Shipment details
        sa.Column("container_number", sa.String(length=50), nullable=False),
        sa.Column("bill_of_lading", sa.String(length=100), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("container_type", sa.String(length=20), nullable=False),
        # Route
        sa.Column("origin_port", sa.String(length=100), nullable=False),
        sa.Column("destination_port", sa.String(length=100), nullable=False),
        sa.Column("current_location", sa.String(length=200), nullable=True),
        # Dates
        sa.Column("departure_date", sa.String(length=50), nullable=True),
        sa.Column("estimated_arrival", sa.String(length=50), nullable=True),
        sa.Column("actual_arrival", sa.String(length=50), nullable=True),
        # Status
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="in_transit",
        ),
        sa.Column("status_updated_at", sa.String(length=50), nullable=True),
        sa.Column("delay_hours", sa.Integer(), nullable=False, server_default="0"),
        # Tracking
        sa.Column("tracking_events", sa.JSON(), nullable=True),
        # Metadata
        sa.Column("notes", sa.String(length=1000), nullable=True),
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

    # Create indexes
    op.create_index(
        "ix_shipments_container_number",
        "shipments",
        ["container_number"],
        unique=True,
    )
    op.create_index(
        "ix_shipments_bill_of_lading", "shipments", ["bill_of_lading"], unique=True
    )
    op.create_index("ix_shipments_status", "shipments", ["status"], unique=False)


def downgrade():
    op.drop_index("ix_shipments_status", table_name="shipments")
    op.drop_index("ix_shipments_bill_of_lading", table_name="shipments")
    op.drop_index("ix_shipments_container_number", table_name="shipments")
    op.drop_table("shipments")
