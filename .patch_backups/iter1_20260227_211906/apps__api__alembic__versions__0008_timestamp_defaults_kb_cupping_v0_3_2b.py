"""Fix timestamp defaults for KB + cupping tables

Revision ID: 0008_timestamp_defaults_kb_cupping_v0_3_2b
Revises: 0007_market_observation_uniques_v0_3_1
Create Date: 2025-12-27
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_timestamp_defaults_kb_cupping_v0_3_2b"
down_revision = "0007_market_observation_uniques_v0_3_1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # Backfill (defensive)
    op.execute("UPDATE knowledge_docs SET created_at = now() WHERE created_at IS NULL;")
    op.execute("UPDATE knowledge_docs SET updated_at = now() WHERE updated_at IS NULL;")
    op.execute(
        "UPDATE cupping_results SET created_at = now() WHERE created_at IS NULL;"
    )
    op.execute(
        "UPDATE cupping_results SET updated_at = now() WHERE updated_at IS NULL;"
    )

    # Add server-side defaults
    op.alter_column(
        "knowledge_docs",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        existing_nullable=False,
    )
    op.alter_column(
        "knowledge_docs",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        existing_nullable=False,
    )

    op.alter_column(
        "cupping_results",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        existing_nullable=False,
    )
    op.alter_column(
        "cupping_results",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        existing_nullable=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.alter_column(
        "knowledge_docs",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )
    op.alter_column(
        "knowledge_docs",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )

    op.alter_column(
        "cupping_results",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )
    op.alter_column(
        "cupping_results",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )
