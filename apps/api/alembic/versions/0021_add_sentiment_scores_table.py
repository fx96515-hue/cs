"""Add missing sentiment_scores table.

Revision ID: 0021_add_sentiment_scores_table
Revises: 0020_full_stack_data_models
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0021_add_sentiment_scores_table"
down_revision = "0020_full_stack_data_models"
branch_labels = None
depends_on = None


def _table_exists(
    inspector: sa.engine.reflection.Inspector, table_name: str
) -> bool:
    return table_name in inspector.get_table_names()


def _index_exists(
    inspector: sa.engine.reflection.Inspector, table_name: str, index_name: str
) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _table_exists(inspector, "sentiment_scores"):
        op.create_table(
            "sentiment_scores",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("region", sa.String(length=128), nullable=True),
            sa.Column("entity_id", sa.Integer(), nullable=True),
            sa.Column("score", sa.Float(), nullable=False),
            sa.Column("label", sa.String(length=16), nullable=False),
            sa.Column("article_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("scored_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
        )

    inspector = inspect(bind)
    if not _index_exists(inspector, "sentiment_scores", "ix_sentiment_scores_region"):
        op.create_index(
            "ix_sentiment_scores_region",
            "sentiment_scores",
            ["region"],
            unique=False,
        )
    if not _index_exists(inspector, "sentiment_scores", "ix_sentiment_scores_entity_id"):
        op.create_index(
            "ix_sentiment_scores_entity_id",
            "sentiment_scores",
            ["entity_id"],
            unique=False,
        )
    if not _index_exists(inspector, "sentiment_scores", "ix_sentiment_scores_scored_at"):
        op.create_index(
            "ix_sentiment_scores_scored_at",
            "sentiment_scores",
            ["scored_at"],
            unique=False,
        )
    if not _index_exists(inspector, "sentiment_scores", "ix_sentiment_region_scored"):
        op.create_index(
            "ix_sentiment_region_scored",
            "sentiment_scores",
            ["region", "scored_at"],
            unique=False,
        )
    if not _index_exists(inspector, "sentiment_scores", "ix_sentiment_entity_scored"):
        op.create_index(
            "ix_sentiment_entity_scored",
            "sentiment_scores",
            ["entity_id", "scored_at"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if _table_exists(inspector, "sentiment_scores"):
        for index_name in (
            "ix_sentiment_entity_scored",
            "ix_sentiment_region_scored",
            "ix_sentiment_scores_scored_at",
            "ix_sentiment_scores_entity_id",
            "ix_sentiment_scores_region",
        ):
            if _index_exists(inspector, "sentiment_scores", index_name):
                op.drop_index(index_name, table_name="sentiment_scores")
                inspector = inspect(bind)
        op.drop_table("sentiment_scores")
