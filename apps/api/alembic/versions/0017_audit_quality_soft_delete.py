"""Add audit logs, entity versions, data quality flags, and soft deletes

Revision ID: 0017_audit_quality_soft_delete
Revises: 0016_add_cooperative_fields_and_regions
Create Date: 2026-02-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0017_audit_quality_soft_delete"
down_revision = "0016_add_cooperative_fields_and_regions"
branch_labels = None
depends_on = None


def _column_exists(
    inspector: sa.engine.reflection.Inspector, table: str, column: str
) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "audit_logs" not in inspector.get_table_names():
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("actor_id", sa.Integer(), nullable=True),
            sa.Column("actor_email", sa.String(length=320), nullable=True),
            sa.Column("actor_role", sa.String(length=32), nullable=True),
            sa.Column("action", sa.String(length=64), nullable=False),
            sa.Column("entity_type", sa.String(length=64), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=True),
            sa.Column("request_id", sa.String(length=64), nullable=True),
            sa.Column("ip_address", sa.String(length=64), nullable=True),
            sa.Column("user_agent", sa.String(length=255), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
        op.create_index(
            "ix_audit_logs_entity_type", "audit_logs", ["entity_type"], unique=False
        )
        op.create_index(
            "ix_audit_logs_entity_id", "audit_logs", ["entity_id"], unique=False
        )
        op.create_index(
            "ix_audit_logs_entity",
            "audit_logs",
            ["entity_type", "entity_id"],
            unique=False,
        )

    if "entity_versions" not in inspector.get_table_names():
        op.create_table(
            "entity_versions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("entity_type", sa.String(length=64), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("changed_by", sa.String(length=320), nullable=True),
            sa.Column("change_reason", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "entity_type", "entity_id", "version", name="uq_entity_version"
            ),
        )
        op.create_index(
            "ix_entity_versions_entity_type",
            "entity_versions",
            ["entity_type"],
            unique=False,
        )
        op.create_index(
            "ix_entity_versions_entity_id",
            "entity_versions",
            ["entity_id"],
            unique=False,
        )
        op.create_index(
            "ix_entity_versions_entity",
            "entity_versions",
            ["entity_type", "entity_id"],
            unique=False,
        )

    if "data_quality_flags" not in inspector.get_table_names():
        op.create_table(
            "data_quality_flags",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("entity_type", sa.String(length=64), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=False),
            sa.Column("field_name", sa.String(length=128), nullable=True),
            sa.Column("issue_type", sa.String(length=64), nullable=False),
            sa.Column(
                "severity", sa.String(length=16), nullable=False, server_default="info"
            ),
            sa.Column("message", sa.String(length=512), nullable=True),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("resolved_by", sa.String(length=255), nullable=True),
            sa.Column("source_id", sa.Integer(), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
        )
        op.create_index(
            "ix_data_quality_flags_entity_type",
            "data_quality_flags",
            ["entity_type"],
            unique=False,
        )
        op.create_index(
            "ix_data_quality_flags_entity_id",
            "data_quality_flags",
            ["entity_id"],
            unique=False,
        )
        op.create_index(
            "ix_data_quality_flags_issue_type",
            "data_quality_flags",
            ["issue_type"],
            unique=False,
        )
        op.create_index(
            "ix_data_quality_flags_severity",
            "data_quality_flags",
            ["severity"],
            unique=False,
        )
        op.create_index(
            "ix_data_quality_flags_entity",
            "data_quality_flags",
            ["entity_type", "entity_id"],
            unique=False,
        )

    for table_name in ["cooperatives", "roasters", "lots", "shipments", "regions"]:
        if table_name in inspector.get_table_names():
            if not _column_exists(inspector, table_name, "deleted_at"):
                op.add_column(
                    table_name,
                    sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
                )
                op.create_index(
                    f"ix_{table_name}_deleted_at",
                    table_name,
                    ["deleted_at"],
                    unique=False,
                )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    for table_name in ["cooperatives", "roasters", "lots", "shipments", "regions"]:
        if table_name in inspector.get_table_names():
            if _column_exists(inspector, table_name, "deleted_at"):
                op.drop_index(f"ix_{table_name}_deleted_at", table_name=table_name)
                op.drop_column(table_name, "deleted_at")

    if "data_quality_flags" in inspector.get_table_names():
        op.drop_index("ix_data_quality_flags_entity", table_name="data_quality_flags")
        op.drop_index("ix_data_quality_flags_severity", table_name="data_quality_flags")
        op.drop_index(
            "ix_data_quality_flags_issue_type", table_name="data_quality_flags"
        )
        op.drop_index(
            "ix_data_quality_flags_entity_id", table_name="data_quality_flags"
        )
        op.drop_index(
            "ix_data_quality_flags_entity_type", table_name="data_quality_flags"
        )
        op.drop_table("data_quality_flags")

    if "entity_versions" in inspector.get_table_names():
        op.drop_index("ix_entity_versions_entity", table_name="entity_versions")
        op.drop_index("ix_entity_versions_entity_id", table_name="entity_versions")
        op.drop_index("ix_entity_versions_entity_type", table_name="entity_versions")
        op.drop_table("entity_versions")

    if "audit_logs" in inspector.get_table_names():
        op.drop_index("ix_audit_logs_entity", table_name="audit_logs")
        op.drop_index("ix_audit_logs_entity_id", table_name="audit_logs")
        op.drop_index("ix_audit_logs_entity_type", table_name="audit_logs")
        op.drop_index("ix_audit_logs_action", table_name="audit_logs")
        op.drop_table("audit_logs")
