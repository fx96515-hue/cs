"""Add deals, price quotes, transport events, and evidence field support

Revision ID: 0019_milestone1_gap_close
Revises: 0018_regions_and_shipment_lots
Create Date: 2026-02-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0019_milestone1_gap_close"
down_revision = "0018_regions_and_shipment_lots"
branch_labels = None
depends_on = None


def _column_exists(
    inspector: sa.engine.reflection.Inspector, table: str, column: str
) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table))


def _fk_exists(
    inspector: sa.engine.reflection.Inspector, table: str, column: str, target: str
) -> bool:
    for fk in inspector.get_foreign_keys(table):
        if column in fk.get("constrained_columns", []) and target in (
            fk.get("referred_table") or ""
        ):
            return True
    return False


def _unique_exists(
    inspector: sa.engine.reflection.Inspector, table: str, name: str
) -> bool:
    return any(uc["name"] == name for uc in inspector.get_unique_constraints(table))


def _fk_constraint_exists(
    inspector: sa.engine.reflection.Inspector, table: str, name: str
) -> bool:
    return any(fk.get("name") == name for fk in inspector.get_foreign_keys(table))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "deals" not in inspector.get_table_names():
        op.create_table(
            "deals",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("cooperative_id", sa.Integer(), nullable=True),
            sa.Column("roaster_id", sa.Integer(), nullable=True),
            sa.Column("lot_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
            sa.Column("incoterm", sa.String(length=16), nullable=True),
            sa.Column("price_per_kg", sa.Float(), nullable=True),
            sa.Column("currency", sa.String(length=8), nullable=True),
            sa.Column("weight_kg", sa.Float(), nullable=True),
            sa.Column("value_total", sa.Float(), nullable=True),
            sa.Column("value_eur", sa.Float(), nullable=True),
            sa.Column("origin_country", sa.String(length=64), nullable=True),
            sa.Column("origin_region", sa.String(length=128), nullable=True),
            sa.Column("variety", sa.String(length=128), nullable=True),
            sa.Column("process_method", sa.String(length=128), nullable=True),
            sa.Column("quality_grade", sa.String(length=64), nullable=True),
            sa.Column("cupping_score", sa.Float(), nullable=True),
            sa.Column("certifications", sa.JSON(), nullable=True),
            sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
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
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["cooperative_id"], ["cooperatives.id"]),
            sa.ForeignKeyConstraint(["roaster_id"], ["roasters.id"]),
            sa.ForeignKeyConstraint(["lot_id"], ["lots.id"]),
        )
        op.create_index("ix_deals_status", "deals", ["status"], unique=False)
        op.create_index("ix_deals_cooperative_id", "deals", ["cooperative_id"], unique=False)
        op.create_index("ix_deals_roaster_id", "deals", ["roaster_id"], unique=False)
        op.create_index("ix_deals_lot_id", "deals", ["lot_id"], unique=False)
        op.create_index("ix_deals_closed_at", "deals", ["closed_at"], unique=False)

    if "price_quotes" not in inspector.get_table_names():
        op.create_table(
            "price_quotes",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("lot_id", sa.Integer(), nullable=True),
            sa.Column("deal_id", sa.Integer(), nullable=True),
            sa.Column("source_id", sa.Integer(), nullable=True),
            sa.Column("price_per_kg", sa.Float(), nullable=False),
            sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
            sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("notes", sa.String(length=500), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
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
            sa.ForeignKeyConstraint(["lot_id"], ["lots.id"]),
            sa.ForeignKeyConstraint(["deal_id"], ["deals.id"]),
            sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        )
        op.create_index("ix_price_quotes_lot_id", "price_quotes", ["lot_id"], unique=False)
        op.create_index("ix_price_quotes_deal_id", "price_quotes", ["deal_id"], unique=False)
        op.create_index("ix_price_quotes_source_id", "price_quotes", ["source_id"], unique=False)
        op.create_index("ix_price_quotes_observed_at", "price_quotes", ["observed_at"], unique=False)

    if "transport_events" not in inspector.get_table_names():
        op.create_table(
            "transport_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("shipment_id", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(length=64), nullable=False),
            sa.Column("location", sa.String(length=200), nullable=True),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(length=64), nullable=True),
            sa.Column("details", sa.JSON(), nullable=True),
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
            sa.ForeignKeyConstraint(["shipment_id"], ["shipments.id"]),
        )
        op.create_index(
            "ix_transport_events_shipment_id",
            "transport_events",
            ["shipment_id"],
            unique=False,
        )
        op.create_index(
            "ix_transport_events_occurred_at",
            "transport_events",
            ["occurred_at"],
            unique=False,
        )

    if "shipments" in inspector.get_table_names():
        if not _column_exists(inspector, "shipments", "departure_at"):
            op.add_column(
                "shipments",
                sa.Column("departure_at", sa.DateTime(timezone=True), nullable=True),
            )
        if not _column_exists(inspector, "shipments", "estimated_arrival_at"):
            op.add_column(
                "shipments",
                sa.Column("estimated_arrival_at", sa.DateTime(timezone=True), nullable=True),
            )
        if not _column_exists(inspector, "shipments", "actual_arrival_at"):
            op.add_column(
                "shipments",
                sa.Column("actual_arrival_at", sa.DateTime(timezone=True), nullable=True),
            )

    if "entity_evidence" in inspector.get_table_names():
        if not _column_exists(inspector, "entity_evidence", "field_name"):
            op.add_column(
                "entity_evidence",
                sa.Column("field_name", sa.String(length=128), nullable=True),
            )
        if _unique_exists(inspector, "entity_evidence", "uq_entity_evidence"):
            op.drop_constraint("uq_entity_evidence", "entity_evidence", type_="unique")
        op.create_unique_constraint(
            "uq_entity_evidence",
            "entity_evidence",
            ["entity_type", "entity_id", "evidence_url", "field_name"],
        )

    if "data_quality_flags" in inspector.get_table_names():
        if _column_exists(inspector, "data_quality_flags", "source_id") and not _fk_exists(
            inspector, "data_quality_flags", "source_id", "sources"
        ):
            op.create_foreign_key(
                "fk_data_quality_flags_source_id",
                "data_quality_flags",
                "sources",
                ["source_id"],
                ["id"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "data_quality_flags" in inspector.get_table_names():
        if _fk_constraint_exists(
            inspector, "data_quality_flags", "fk_data_quality_flags_source_id"
        ):
            op.drop_constraint(
                "fk_data_quality_flags_source_id",
                "data_quality_flags",
                type_="foreignkey",
            )

    if "entity_evidence" in inspector.get_table_names():
        if _unique_exists(inspector, "entity_evidence", "uq_entity_evidence"):
            op.drop_constraint("uq_entity_evidence", "entity_evidence", type_="unique")
        op.create_unique_constraint(
            "uq_entity_evidence",
            "entity_evidence",
            ["entity_type", "entity_id", "evidence_url"],
        )
        if _column_exists(inspector, "entity_evidence", "field_name"):
            op.drop_column("entity_evidence", "field_name")

    if "shipments" in inspector.get_table_names():
        if _column_exists(inspector, "shipments", "actual_arrival_at"):
            op.drop_column("shipments", "actual_arrival_at")
        if _column_exists(inspector, "shipments", "estimated_arrival_at"):
            op.drop_column("shipments", "estimated_arrival_at")
        if _column_exists(inspector, "shipments", "departure_at"):
            op.drop_column("shipments", "departure_at")

    if "transport_events" in inspector.get_table_names():
        op.drop_index("ix_transport_events_occurred_at", table_name="transport_events")
        op.drop_index("ix_transport_events_shipment_id", table_name="transport_events")
        op.drop_table("transport_events")

    if "price_quotes" in inspector.get_table_names():
        op.drop_index("ix_price_quotes_observed_at", table_name="price_quotes")
        op.drop_index("ix_price_quotes_source_id", table_name="price_quotes")
        op.drop_index("ix_price_quotes_deal_id", table_name="price_quotes")
        op.drop_index("ix_price_quotes_lot_id", table_name="price_quotes")
        op.drop_table("price_quotes")

    if "deals" in inspector.get_table_names():
        op.drop_index("ix_deals_closed_at", table_name="deals")
        op.drop_index("ix_deals_lot_id", table_name="deals")
        op.drop_index("ix_deals_roaster_id", table_name="deals")
        op.drop_index("ix_deals_cooperative_id", table_name="deals")
        op.drop_index("ix_deals_status", table_name="deals")
        op.drop_table("deals")
