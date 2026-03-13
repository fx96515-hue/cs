"""Add deals, price quotes, transport events, and evidence field support.

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


def _create_deals_table(inspector: sa.engine.reflection.Inspector) -> None:
    if "deals" in inspector.get_table_names():
        return

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
    for index_name, columns in (
        ("ix_deals_status", ["status"]),
        ("ix_deals_cooperative_id", ["cooperative_id"]),
        ("ix_deals_roaster_id", ["roaster_id"]),
        ("ix_deals_lot_id", ["lot_id"]),
        ("ix_deals_closed_at", ["closed_at"]),
    ):
        op.create_index(index_name, "deals", columns, unique=False)


def _create_price_quotes_table(inspector: sa.engine.reflection.Inspector) -> None:
    if "price_quotes" in inspector.get_table_names():
        return

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
    for index_name, columns in (
        ("ix_price_quotes_lot_id", ["lot_id"]),
        ("ix_price_quotes_deal_id", ["deal_id"]),
        ("ix_price_quotes_source_id", ["source_id"]),
        ("ix_price_quotes_observed_at", ["observed_at"]),
    ):
        op.create_index(index_name, "price_quotes", columns, unique=False)


def _create_transport_events_table(inspector: sa.engine.reflection.Inspector) -> None:
    if "transport_events" in inspector.get_table_names():
        return

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
    for index_name, columns in (
        ("ix_transport_events_shipment_id", ["shipment_id"]),
        ("ix_transport_events_occurred_at", ["occurred_at"]),
    ):
        op.create_index(index_name, "transport_events", columns, unique=False)


def _ensure_shipment_columns(inspector: sa.engine.reflection.Inspector) -> None:
    if "shipments" not in inspector.get_table_names():
        return

    for column_name in ("departure_at", "estimated_arrival_at", "actual_arrival_at"):
        if not _column_exists(inspector, "shipments", column_name):
            op.add_column(
                "shipments",
                sa.Column(column_name, sa.DateTime(timezone=True), nullable=True),
            )


def _ensure_entity_evidence_constraint(inspector: sa.engine.reflection.Inspector) -> None:
    if "entity_evidence" not in inspector.get_table_names():
        return

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


def _ensure_data_quality_fk(inspector: sa.engine.reflection.Inspector) -> None:
    if "data_quality_flags" not in inspector.get_table_names():
        return

    has_source_id = _column_exists(inspector, "data_quality_flags", "source_id")
    has_fk = _fk_exists(inspector, "data_quality_flags", "source_id", "sources")
    if has_source_id and not has_fk:
        op.create_foreign_key(
            "fk_data_quality_flags_source_id",
            "data_quality_flags",
            "sources",
            ["source_id"],
            ["id"],
        )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    _create_deals_table(inspector)
    _create_price_quotes_table(inspector)
    _create_transport_events_table(inspector)
    _ensure_shipment_columns(inspector)
    _ensure_entity_evidence_constraint(inspector)
    _ensure_data_quality_fk(inspector)


def _drop_data_quality_fk(inspector: sa.engine.reflection.Inspector) -> None:
    if "data_quality_flags" not in inspector.get_table_names():
        return
    if _fk_constraint_exists(
        inspector, "data_quality_flags", "fk_data_quality_flags_source_id"
    ):
        op.drop_constraint(
            "fk_data_quality_flags_source_id",
            "data_quality_flags",
            type_="foreignkey",
        )


def _restore_entity_evidence_constraint(
    inspector: sa.engine.reflection.Inspector,
) -> None:
    if "entity_evidence" not in inspector.get_table_names():
        return

    if _unique_exists(inspector, "entity_evidence", "uq_entity_evidence"):
        op.drop_constraint("uq_entity_evidence", "entity_evidence", type_="unique")
    op.create_unique_constraint(
        "uq_entity_evidence",
        "entity_evidence",
        ["entity_type", "entity_id", "evidence_url"],
    )
    if _column_exists(inspector, "entity_evidence", "field_name"):
        op.drop_column("entity_evidence", "field_name")


def _drop_shipment_columns(inspector: sa.engine.reflection.Inspector) -> None:
    if "shipments" not in inspector.get_table_names():
        return

    for column_name in ("actual_arrival_at", "estimated_arrival_at", "departure_at"):
        if _column_exists(inspector, "shipments", column_name):
            op.drop_column("shipments", column_name)


def _drop_transport_events_table(inspector: sa.engine.reflection.Inspector) -> None:
    if "transport_events" not in inspector.get_table_names():
        return
    op.drop_index("ix_transport_events_occurred_at", table_name="transport_events")
    op.drop_index("ix_transport_events_shipment_id", table_name="transport_events")
    op.drop_table("transport_events")


def _drop_price_quotes_table(inspector: sa.engine.reflection.Inspector) -> None:
    if "price_quotes" not in inspector.get_table_names():
        return
    op.drop_index("ix_price_quotes_observed_at", table_name="price_quotes")
    op.drop_index("ix_price_quotes_source_id", table_name="price_quotes")
    op.drop_index("ix_price_quotes_deal_id", table_name="price_quotes")
    op.drop_index("ix_price_quotes_lot_id", table_name="price_quotes")
    op.drop_table("price_quotes")


def _drop_deals_table(inspector: sa.engine.reflection.Inspector) -> None:
    if "deals" not in inspector.get_table_names():
        return
    op.drop_index("ix_deals_closed_at", table_name="deals")
    op.drop_index("ix_deals_lot_id", table_name="deals")
    op.drop_index("ix_deals_roaster_id", table_name="deals")
    op.drop_index("ix_deals_cooperative_id", table_name="deals")
    op.drop_index("ix_deals_status", table_name="deals")
    op.drop_table("deals")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    _drop_data_quality_fk(inspector)
    _restore_entity_evidence_constraint(inspector)
    _drop_shipment_columns(inspector)
    _drop_transport_events_table(inspector)
    _drop_price_quotes_table(inspector)
    _drop_deals_table(inspector)
