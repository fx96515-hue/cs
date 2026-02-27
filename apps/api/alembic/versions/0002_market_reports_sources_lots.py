"""Market observations, sources, reports, lots, margin runs + workflow fields

Revision ID: 0002_market_reports_sources_lots
Revises: 0001_init
Create Date: 2025-12-22

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_market_reports_sources_lots"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade():
    # --- workflow fields ---
    op.add_column(
        "cooperatives",
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="active"
        ),
    )
    op.add_column(
        "cooperatives", sa.Column("next_action", sa.String(length=255), nullable=True)
    )
    op.add_column("cooperatives", sa.Column("requested_data", sa.Text(), nullable=True))
    op.add_column(
        "cooperatives",
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "cooperatives",
        sa.Column("last_scored_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_cooperatives_status", "cooperatives", ["status"], unique=False)

    op.add_column(
        "roasters",
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="active"
        ),
    )
    op.add_column(
        "roasters", sa.Column("next_action", sa.String(length=255), nullable=True)
    )
    op.add_column("roasters", sa.Column("requested_data", sa.Text(), nullable=True))
    op.add_column(
        "roasters",
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "roasters",
        sa.Column("last_scored_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("roasters", sa.Column("total_score", sa.Float(), nullable=True))
    op.add_column("roasters", sa.Column("confidence", sa.Float(), nullable=True))
    op.create_index("ix_roasters_status", "roasters", ["status"], unique=False)

    # --- sources ---
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2000), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False, server_default="web"),
        sa.Column("reliability", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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

    # --- market observations ---
    op.create_table(
        "market_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=True
        ),
        sa.Column("raw_text", sa.Text(), nullable=True),
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
    )
    op.create_index(
        "ix_market_observations_key", "market_observations", ["key"], unique=False
    )
    op.create_index(
        "ix_market_observations_observed_at",
        "market_observations",
        ["observed_at"],
        unique=False,
    )
    op.create_index(
        "ix_market_key_observed_at",
        "market_observations",
        ["key", "observed_at"],
        unique=False,
    )

    # --- reports ---
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(length=32), nullable=False, server_default="daily"),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("report_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("markdown", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
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
    op.create_index("ix_reports_report_at", "reports", ["report_at"], unique=False)
    op.create_index(
        "ix_reports_kind_report_at", "reports", ["kind", "report_at"], unique=False
    )

    # --- lots ---
    op.create_table(
        "lots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "cooperative_id",
            sa.Integer(),
            sa.ForeignKey("cooperatives.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("crop_year", sa.Integer(), nullable=True),
        sa.Column("incoterm", sa.String(length=16), nullable=True),
        sa.Column("price_per_kg", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("expected_cupping_score", sa.Float(), nullable=True),
        sa.Column("varieties", sa.String(length=255), nullable=True),
        sa.Column("processing", sa.String(length=64), nullable=True),
        sa.Column("availability_window", sa.String(length=64), nullable=True),
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
    )
    op.create_index("ix_lots_cooperative_id", "lots", ["cooperative_id"], unique=False)
    op.create_index(
        "ix_lots_coop_name", "lots", ["cooperative_id", "name"], unique=False
    )

    # --- margin runs ---
    op.create_table(
        "margin_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lot_id", sa.Integer(), sa.ForeignKey("lots.id"), nullable=False),
        sa.Column(
            "profile",
            sa.String(length=64),
            nullable=False,
            server_default="conservative",
        ),
        sa.Column("inputs", sa.JSON(), nullable=False),
        sa.Column("outputs", sa.JSON(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
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
    op.create_index("ix_margin_runs_lot_id", "margin_runs", ["lot_id"], unique=False)
    op.create_index(
        "ix_margin_runs_computed_at", "margin_runs", ["computed_at"], unique=False
    )
    op.create_index(
        "ix_margin_runs_lot_profile", "margin_runs", ["lot_id", "profile"], unique=False
    )


def downgrade():
    op.drop_index("ix_margin_runs_lot_profile", table_name="margin_runs")
    op.drop_index("ix_margin_runs_computed_at", table_name="margin_runs")
    op.drop_index("ix_margin_runs_lot_id", table_name="margin_runs")
    op.drop_table("margin_runs")

    op.drop_index("ix_lots_coop_name", table_name="lots")
    op.drop_index("ix_lots_cooperative_id", table_name="lots")
    op.drop_table("lots")

    op.drop_index("ix_reports_kind_report_at", table_name="reports")
    op.drop_index("ix_reports_report_at", table_name="reports")
    op.drop_table("reports")

    op.drop_index("ix_market_key_observed_at", table_name="market_observations")
    op.drop_index(
        "ix_market_observations_observed_at", table_name="market_observations"
    )
    op.drop_index("ix_market_observations_key", table_name="market_observations")
    op.drop_table("market_observations")

    op.drop_table("sources")

    op.drop_index("ix_roasters_status", table_name="roasters")
    op.drop_column("roasters", "confidence")
    op.drop_column("roasters", "total_score")
    op.drop_column("roasters", "last_scored_at")
    op.drop_column("roasters", "last_verified_at")
    op.drop_column("roasters", "requested_data")
    op.drop_column("roasters", "next_action")
    op.drop_column("roasters", "status")

    op.drop_index("ix_cooperatives_status", table_name="cooperatives")
    op.drop_column("cooperatives", "last_scored_at")
    op.drop_column("cooperatives", "last_verified_at")
    op.drop_column("cooperatives", "requested_data")
    op.drop_column("cooperatives", "next_action")
    op.drop_column("cooperatives", "status")
