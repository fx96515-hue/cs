"""Add pgvector extension and embedding columns

Revision ID: 0013_add_pgvector_embeddings
Revises: 0012_add_quality_alerts_table
Create Date: 2026-02-12

"""

import warnings

from alembic import op
import sqlalchemy as sa


revision = "0013_add_pgvector_embeddings"
down_revision = "0012_add_quality_alerts_table"
branch_labels = None
depends_on = None


def upgrade():
    # Try to enable pgvector - skip gracefully if not available (CI environment)
    # Use SAVEPOINT to avoid poisoning the outer transaction on failure
    conn = op.get_bind()
    try:
        conn.execute(sa.text("SAVEPOINT pgvector_check"))
        conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(sa.text("RELEASE SAVEPOINT pgvector_check"))
    except Exception as e:
        # Rollback to savepoint to keep transaction clean
        try:
            conn.execute(sa.text("ROLLBACK TO SAVEPOINT pgvector_check"))
        except Exception:
            # If rollback fails, the savepoint may not exist (e.g., in autocommit mode)
            pass
        warnings.warn(
            f"pgvector extension not available - skipping vector columns and indexes. "
            f"Semantic search features will be unavailable. "
            f"Error: {type(e).__name__}: {str(e)}"
        )
        return

    # Add embedding columns and indexes only if extension is available
    op.execute(
        """ALTER TABLE cooperatives ADD COLUMN IF NOT EXISTS embedding vector(1536)"""
    )
    op.execute(
        """ALTER TABLE roasters ADD COLUMN IF NOT EXISTS embedding vector(1536)"""
    )
    op.execute(
        """CREATE INDEX IF NOT EXISTS ix_cooperatives_embedding_cosine ON cooperatives USING hnsw (embedding vector_cosine_ops)"""
    )
    op.execute(
        """CREATE INDEX IF NOT EXISTS ix_roasters_embedding_cosine ON roasters USING hnsw (embedding vector_cosine_ops)"""
    )


def downgrade():
    # Drop indexes first
    op.execute("DROP INDEX IF EXISTS ix_roasters_embedding_cosine")
    op.execute("DROP INDEX IF EXISTS ix_cooperatives_embedding_cosine")

    # Drop columns
    op.execute("ALTER TABLE roasters DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE cooperatives DROP COLUMN IF EXISTS embedding")

    # Note: We don't drop the vector extension as it might be used by other tables
    # If you really need to drop it, uncomment the next line:
    # op.execute("DROP EXTENSION IF EXISTS vector")
