"""Resize embedding columns from vector(1536) to vector(384) for local model

Revision ID: 0014_resize_embedding_to_384
Revises: 0013_add_pgvector_embeddings
Create Date: 2026-02-24

"""

import warnings

from alembic import op
import sqlalchemy as sa


revision = "0014_resize_embedding_to_384"
down_revision = "0013_add_pgvector_embeddings"
branch_labels = None
depends_on = None


def _pgvector_available(conn) -> bool:
    """Return True if the vector type exists in this database."""
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
    )
    return result.fetchone() is not None


def upgrade():
    conn = op.get_bind()

    if not _pgvector_available(conn):
        warnings.warn(
            "pgvector extension not available â€“ skipping embedding column resize. "
            "Semantic search features will be unavailable."
        )
        return

    # Drop existing HNSW indexes (they are tied to the old dimensionality)
    op.execute("DROP INDEX IF EXISTS ix_cooperatives_embedding_cosine")
    op.execute("DROP INDEX IF EXISTS ix_roasters_embedding_cosine")

    # Alter column type to vector(384).
    # pgvector requires USING clause for the cast.
    op.execute(
        """ALTER TABLE cooperatives
           ALTER COLUMN embedding TYPE vector(384)
           USING embedding::text::vector(384)"""
    )
    op.execute(
        """ALTER TABLE roasters
           ALTER COLUMN embedding TYPE vector(384)
           USING embedding::text::vector(384)"""
    )

    # Recreate HNSW indexes for the new dimensionality
    op.execute(
        """CREATE INDEX IF NOT EXISTS ix_cooperatives_embedding_cosine
           ON cooperatives USING hnsw (embedding vector_cosine_ops)"""
    )
    op.execute(
        """CREATE INDEX IF NOT EXISTS ix_roasters_embedding_cosine
           ON roasters USING hnsw (embedding vector_cosine_ops)"""
    )


def downgrade():
    conn = op.get_bind()

    if not _pgvector_available(conn):
        warnings.warn(
            "pgvector extension not available â€“ skipping embedding column downgrade."
        )
        return

    # Drop indexes first
    op.execute("DROP INDEX IF EXISTS ix_cooperatives_embedding_cosine")
    op.execute("DROP INDEX IF EXISTS ix_roasters_embedding_cosine")

    # Revert column type back to vector(1536)
    op.execute(
        """ALTER TABLE cooperatives
           ALTER COLUMN embedding TYPE vector(1536)
           USING embedding::text::vector(1536)"""
    )
    op.execute(
        """ALTER TABLE roasters
           ALTER COLUMN embedding TYPE vector(1536)
           USING embedding::text::vector(1536)"""
    )

    # Recreate HNSW indexes for vector(1536)
    op.execute(
        """CREATE INDEX IF NOT EXISTS ix_cooperatives_embedding_cosine
           ON cooperatives USING hnsw (embedding vector_cosine_ops)"""
    )
    op.execute(
        """CREATE INDEX IF NOT EXISTS ix_roasters_embedding_cosine
           ON roasters USING hnsw (embedding vector_cosine_ops)"""
    )
