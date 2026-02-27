"""market observation unique constraint

Revision ID: 0007_market_observation_uniques_v0_3_1
Revises: 0006_kb_and_cupping_v0_3_0
Create Date: 2025-12-23

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "0007_market_observation_uniques_v0_3_1"
down_revision = "0006_kb_and_cupping_v0_3_0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # IMPORTANT (Postgres): Alembic's default version table column is VARCHAR(32).
    # Our human-readable revision ids can exceed 32 chars, which breaks upgrades
    # when Alembic tries to write the new revision into the version table.
    #
    # Fix: enlarge the column before Alembic updates alembic_version.version_num.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255);"
        )

    # Ensure idempotent market ingest: one observation per key+time+source.
    # (source_id can be NULL; Postgres treats NULLs as distinct, so we also
    # recommend always setting a source_id for ingested data.)
    op.create_unique_constraint(
        "uq_market_observations_key_observed_at_source_id",
        "market_observations",
        ["key", "observed_at", "source_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_market_observations_key_observed_at_source_id",
        "market_observations",
        type_="unique",
    )
