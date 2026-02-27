"""Add roaster contact email

Revision ID: 0004_roaster_contact_email
Revises: 0003_entity_evidence
Create Date: 2025-12-22

"""

from alembic import op
import sqlalchemy as sa


revision = "0004_roaster_contact_email"
down_revision = "0003_entity_evidence"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "roasters", sa.Column("contact_email", sa.String(length=320), nullable=True)
    )
    op.create_index(
        "ix_roasters_contact_email", "roasters", ["contact_email"], unique=False
    )


def downgrade():
    op.drop_index("ix_roasters_contact_email", table_name="roasters")
    op.drop_column("roasters", "contact_email")
