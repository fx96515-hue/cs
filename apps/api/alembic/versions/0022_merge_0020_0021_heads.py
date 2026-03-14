"""Merge heads for 0020 full stack models and 0021 sentiment table.

Revision ID: 0022_merge_0020_0021_heads
Revises: 0020_full_stack_data_models, 0021_add_sentiment_scores_table
Create Date: 2026-03-14
"""

from alembic import op

revision = "0022_merge_0020_0021_heads"
down_revision = ("0020_full_stack_data_models", "0021_add_sentiment_scores_table")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge migration: intentionally no DDL.
    pass


def downgrade() -> None:
    # Merge migration: intentionally no DDL.
    pass
