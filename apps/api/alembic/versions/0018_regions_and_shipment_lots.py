"""Add cooperative region FK and shipment_lots join table

Revision ID: 0018_regions_and_shipment_lots
Revises: 0017_audit_quality_soft_delete
Create Date: 2026-02-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0018_regions_and_shipment_lots"
down_revision = "0017_audit_quality_soft_delete"
branch_labels = None
depends_on = None


def _column_exists(
    inspector: sa.engine.reflection.Inspector, table: str, column: str
) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table))


def _fk_constraint_exists(
    inspector: sa.engine.reflection.Inspector, table: str, constraint_name: str
) -> bool:
    return any(
        fk.get("name") == constraint_name for fk in inspector.get_foreign_keys(table)
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "shipment_lots" not in inspector.get_table_names():
        op.create_table(
            "shipment_lots",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("shipment_id", sa.Integer(), nullable=False),
            sa.Column("lot_id", sa.Integer(), nullable=False),
            sa.Column("weight_kg", sa.Float(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["shipment_id"], ["shipments.id"]),
            sa.ForeignKeyConstraint(["lot_id"], ["lots.id"]),
            sa.UniqueConstraint("shipment_id", "lot_id", name="uq_shipment_lot"),
        )
        op.create_index(
            "ix_shipment_lots_shipment_id",
            "shipment_lots",
            ["shipment_id"],
            unique=False,
        )
        op.create_index(
            "ix_shipment_lots_lot_id", "shipment_lots", ["lot_id"], unique=False
        )

    if "cooperatives" in inspector.get_table_names():
        if not _column_exists(inspector, "cooperatives", "region_id"):
            op.add_column(
                "cooperatives",
                sa.Column("region_id", sa.Integer(), nullable=True),
            )
            op.create_index(
                "ix_cooperatives_region_id",
                "cooperatives",
                ["region_id"],
                unique=False,
            )
            if "regions" in inspector.get_table_names():
                op.create_foreign_key(
                    "fk_cooperatives_region_id",
                    "cooperatives",
                    "regions",
                    ["region_id"],
                    ["id"],
                )

    if "coffee_price_history" in inspector.get_table_names():
        if not _column_exists(inspector, "coffee_price_history", "market_key"):
            op.add_column(
                "coffee_price_history",
                sa.Column("market_key", sa.String(length=64), nullable=True),
            )
            op.create_index(
                "ix_coffee_price_history_market_key",
                "coffee_price_history",
                ["market_key"],
                unique=False,
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "cooperatives" in inspector.get_table_names():
        if _column_exists(inspector, "cooperatives", "region_id"):
            op.drop_index("ix_cooperatives_region_id", table_name="cooperatives")
            if _fk_constraint_exists(
                inspector, "cooperatives", "fk_cooperatives_region_id"
            ):
                op.drop_constraint("fk_cooperatives_region_id", "cooperatives", type_="foreignkey")
            op.drop_column("cooperatives", "region_id")

    if "coffee_price_history" in inspector.get_table_names():
        if _column_exists(inspector, "coffee_price_history", "market_key"):
            op.drop_index(
                "ix_coffee_price_history_market_key",
                table_name="coffee_price_history",
            )
            op.drop_column("coffee_price_history", "market_key")

    if "shipment_lots" in inspector.get_table_names():
        op.drop_index("ix_shipment_lots_lot_id", table_name="shipment_lots")
        op.drop_index("ix_shipment_lots_shipment_id", table_name="shipment_lots")
        op.drop_table("shipment_lots")
