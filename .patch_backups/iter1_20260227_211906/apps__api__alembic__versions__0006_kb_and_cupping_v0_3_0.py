"""KB documents + cupping results

Revision ID: 0006_kb_and_cupping_v0_3_0
Revises: 0005_data_backbone_v0_3_0
Create Date: 2025-12-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_kb_and_cupping_v0_3_0"
down_revision = "0005_data_backbone_v0_3_0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "knowledge_docs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False, server_default="de"),
        sa.Column("content_md", sa.Text(), nullable=False),
        sa.Column("sources", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("category", "key", "language", name="uq_kb_cat_key_lang"),
    )
    op.create_index(
        "ix_knowledge_docs_category", "knowledge_docs", ["category"], unique=False
    )

    op.create_table(
        "cupping_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("taster", sa.String(length=255), nullable=True),
        sa.Column(
            "cooperative_id",
            sa.Integer(),
            sa.ForeignKey("cooperatives.id"),
            nullable=True,
        ),
        sa.Column("lot_id", sa.Integer(), sa.ForeignKey("lots.id"), nullable=True),
        sa.Column(
            "roaster_id", sa.Integer(), sa.ForeignKey("roasters.id"), nullable=True
        ),
        sa.Column("sca_score", sa.Float(), nullable=True),
        sa.Column("aroma", sa.Float(), nullable=True),
        sa.Column("flavor", sa.Float(), nullable=True),
        sa.Column("aftertaste", sa.Float(), nullable=True),
        sa.Column("acidity", sa.Float(), nullable=True),
        sa.Column("body", sa.Float(), nullable=True),
        sa.Column("balance", sa.Float(), nullable=True),
        sa.Column("sweetness", sa.Float(), nullable=True),
        sa.Column("uniformity", sa.Float(), nullable=True),
        sa.Column("clean_cup", sa.Float(), nullable=True),
        sa.Column("descriptors", sa.String(length=512), nullable=True),
        sa.Column("defects", sa.String(length=512), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_cupping_results_cooperative_id",
        "cupping_results",
        ["cooperative_id"],
        unique=False,
    )
    op.create_index(
        "ix_cupping_results_lot_id", "cupping_results", ["lot_id"], unique=False
    )
    op.create_index(
        "ix_cupping_results_roaster_id", "cupping_results", ["roaster_id"], unique=False
    )
    op.create_index("ix_cupping_score", "cupping_results", ["sca_score"], unique=False)


def downgrade():
    op.drop_index("ix_cupping_score", table_name="cupping_results")
    op.drop_index("ix_cupping_results_roaster_id", table_name="cupping_results")
    op.drop_index("ix_cupping_results_lot_id", table_name="cupping_results")
    op.drop_index("ix_cupping_results_cooperative_id", table_name="cupping_results")
    op.drop_table("cupping_results")

    op.drop_index("ix_knowledge_docs_category", table_name="knowledge_docs")
    op.drop_table("knowledge_docs")
