"""Add sentiment_scores table.

Revision ID: 0021_add_sentiment_scores_table
Revises: 0019_milestone1_gap_close
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0021_add_sentiment_scores_table"
down_revision = "0019_milestone1_gap_close"
branch_labels = None
depends_on = None


def _index_exists(
    inspector: sa.engine.reflection.Inspector, table: str, name: str
) -> bool:
    return any(ix["name"] == name for ix in inspector.get_indexes(table))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "sentiment_scores" not in inspector.get_table_names():
        op.create_table(
            "sentiment_scores",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("region", sa.String(length=128), nullable=True),
            sa.Column("entity_id", sa.Integer(), nullable=True),
            sa.Column("score", sa.Float(), nullable=False),
            sa.Column("label", sa.String(length=16), nullable=False),
            sa.Column(
                "article_count",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column("scored_at", sa.DateTime(timezone=True), nullable=False),
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

    inspector = inspect(bind)
    for index_name, columns in (
        ("ix_sentiment_scores_region", ["region"]),
        ("ix_sentiment_scores_entity_id", ["entity_id"]),
        ("ix_sentiment_scores_scored_at", ["scored_at"]),
        ("ix_sentiment_region_scored", ["region", "scored_at"]),
        ("ix_sentiment_entity_scored", ["entity_id", "scored_at"]),
    ):
        if not _index_exists(inspector, "sentiment_scores", index_name):
            op.create_index(index_name, "sentiment_scores", columns, unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "sentiment_scores" in inspector.get_table_names():
        op.drop_table("sentiment_scores")
