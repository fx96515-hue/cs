"""Entity evidence/provenance table

Revision ID: 0003_entity_evidence
Revises: 0002_market_reports_sources_lots
Create Date: 2025-12-22

"""

from alembic import op
import sqlalchemy as sa


revision = "0003_entity_evidence"
down_revision = "0002_market_reports_sources_lots"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "entity_evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("evidence_url", sa.String(length=1000), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "entity_type", "entity_id", "evidence_url", name="uq_entity_evidence"
        ),
    )
    op.create_index(
        "ix_entity_evidence_entity_id", "entity_evidence", ["entity_id"], unique=False
    )
    op.create_index(
        "ix_entity_evidence_source_id", "entity_evidence", ["source_id"], unique=False
    )


def downgrade():
    op.drop_index("ix_entity_evidence_source_id", table_name="entity_evidence")
    op.drop_index("ix_entity_evidence_entity_id", table_name="entity_evidence")
    op.drop_table("entity_evidence")
