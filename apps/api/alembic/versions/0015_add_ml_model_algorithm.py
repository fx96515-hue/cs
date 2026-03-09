"""Add algorithm column to ml_models

Revision ID: 0015_add_ml_model_algorithm
Revises: 0014_resize_embedding_to_384
Create Date: 2026-02-25
"""

from alembic import op
import sqlalchemy as sa

revision = "0015_add_ml_model_algorithm"
down_revision = "0014_resize_embedding_to_384"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ml_models",
        sa.Column("algorithm", sa.String(32), nullable=True),
    )
    # Back-fill existing rows with 'random_forest' (original implementation)
    op.execute(
        "UPDATE ml_models SET algorithm = 'random_forest' WHERE algorithm IS NULL"
    )


def downgrade() -> None:
    op.drop_column("ml_models", "algorithm")
