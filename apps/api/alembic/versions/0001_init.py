"""
init

Revision ID: 0001_init
Revises:
Create Date: 2025-12-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

NOW = sa.text("now()")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "cooperatives",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("region", sa.String(length=255), nullable=True),
        sa.Column("altitude_m", sa.Float, nullable=True),
        sa.Column("varieties", sa.String(length=255), nullable=True),
        sa.Column("certifications", sa.String(length=255), nullable=True),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("quality_score", sa.Float, nullable=True),
        sa.Column("reliability_score", sa.Float, nullable=True),
        sa.Column("economics_score", sa.Float, nullable=True),
        sa.Column("total_score", sa.Float, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("meta", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index("ix_cooperatives_name", "cooperatives", ["name"])

    op.create_table(
        "roasters",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=255), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("peru_focus", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("specialty_focus", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("price_position", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("meta", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index("ix_roasters_name", "roasters", ["name"])


def downgrade() -> None:
    op.drop_index("ix_roasters_name", table_name="roasters")
    op.drop_table("roasters")
    op.drop_index("ix_cooperatives_name", table_name="cooperatives")
    op.drop_table("cooperatives")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")