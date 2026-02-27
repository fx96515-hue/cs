"""Data backbone: web extracts, news, regions, aliases, events

Revision ID: 0005_data_backbone_v0_3_0
Revises: 0004_roaster_contact_email
Create Date: 2025-12-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_data_backbone_v0_3_0"
down_revision = "0004_roaster_contact_email"
branch_labels = None
depends_on = None


def upgrade():
    # --- Extend entity_evidence ---
    op.add_column(
        "entity_evidence",
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("entity_evidence", sa.Column("confidence", sa.Float(), nullable=True))
    op.add_column(
        "entity_evidence", sa.Column("extractor", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "entity_evidence",
        sa.Column("snippet_hash", sa.String(length=64), nullable=True),
    )

    # --- Entity aliases ---
    op.create_table(
        "entity_aliases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "entity_type", "entity_id", "alias", name="uq_entity_alias"
        ),
    )
    op.create_index(
        "ix_entity_aliases_entity_type", "entity_aliases", ["entity_type"], unique=False
    )
    op.create_index(
        "ix_entity_aliases_entity_id", "entity_aliases", ["entity_id"], unique=False
    )

    # --- Entity events ---
    op.create_table(
        "entity_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
    )
    op.create_index(
        "ix_entity_events_entity_type", "entity_events", ["entity_type"], unique=False
    )
    op.create_index(
        "ix_entity_events_entity_id", "entity_events", ["entity_id"], unique=False
    )
    op.create_index(
        "ix_entity_events_event_type", "entity_events", ["event_type"], unique=False
    )
    op.create_index(
        "ix_entity_events_entity_type_id",
        "entity_events",
        ["entity_type", "entity_id"],
        unique=False,
    )

    # --- Web extracts ---
    op.create_table(
        "web_extracts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ok"),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("lang", sa.String(length=16), nullable=True),
        sa.Column("extracted_json", sa.JSON(), nullable=True),
        sa.Column("translated_de", sa.JSON(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.UniqueConstraint("entity_type", "entity_id", "url", name="uq_web_extract"),
    )
    op.create_index(
        "ix_web_extracts_entity_type", "web_extracts", ["entity_type"], unique=False
    )
    op.create_index(
        "ix_web_extracts_entity_id", "web_extracts", ["entity_id"], unique=False
    )
    op.create_index(
        "ix_web_extracts_retrieved_at", "web_extracts", ["retrieved_at"], unique=False
    )
    op.create_index(
        "ix_web_extracts_entity_type_id",
        "web_extracts",
        ["entity_type", "entity_id"],
        unique=False,
    )

    # --- News items ---
    op.create_table(
        "news_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("country", sa.String(length=8), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.UniqueConstraint("url", name="uq_news_url"),
    )
    op.create_index("ix_news_items_topic", "news_items", ["topic"], unique=False)
    op.create_index("ix_news_items_country", "news_items", ["country"], unique=False)
    op.create_index(
        "ix_news_items_published_at", "news_items", ["published_at"], unique=False
    )
    op.create_index(
        "ix_news_items_retrieved_at", "news_items", ["retrieved_at"], unique=False
    )
    op.create_index(
        "ix_news_topic_retrieved", "news_items", ["topic", "retrieved_at"], unique=False
    )

    # --- Peru regions KB ---
    op.create_table(
        "peru_regions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("description_de", sa.Text(), nullable=True),
        sa.Column("typical_varieties", sa.Text(), nullable=True),
        sa.Column("typical_processing", sa.Text(), nullable=True),
        sa.Column("altitude_range", sa.String(length=64), nullable=True),
        sa.Column("logistics_notes", sa.Text(), nullable=True),
        sa.Column("risk_notes", sa.Text(), nullable=True),
        sa.Column("sources", sa.JSON(), nullable=True),
        sa.UniqueConstraint("code", name="uq_peru_region_code"),
    )


def downgrade():
    op.drop_table("peru_regions")
    op.drop_index("ix_news_topic_retrieved", table_name="news_items")
    op.drop_index("ix_news_items_retrieved_at", table_name="news_items")
    op.drop_index("ix_news_items_published_at", table_name="news_items")
    op.drop_index("ix_news_items_country", table_name="news_items")
    op.drop_index("ix_news_items_topic", table_name="news_items")
    op.drop_table("news_items")
    op.drop_index("ix_web_extracts_entity_type_id", table_name="web_extracts")
    op.drop_index("ix_web_extracts_retrieved_at", table_name="web_extracts")
    op.drop_index("ix_web_extracts_entity_id", table_name="web_extracts")
    op.drop_index("ix_web_extracts_entity_type", table_name="web_extracts")
    op.drop_table("web_extracts")
    op.drop_index("ix_entity_events_entity_type_id", table_name="entity_events")
    op.drop_index("ix_entity_events_event_type", table_name="entity_events")
    op.drop_index("ix_entity_events_entity_id", table_name="entity_events")
    op.drop_index("ix_entity_events_entity_type", table_name="entity_events")
    op.drop_table("entity_events")
    op.drop_index("ix_entity_aliases_entity_id", table_name="entity_aliases")
    op.drop_index("ix_entity_aliases_entity_type", table_name="entity_aliases")
    op.drop_table("entity_aliases")

    op.drop_column("entity_evidence", "snippet_hash")
    op.drop_column("entity_evidence", "extractor")
    op.drop_column("entity_evidence", "confidence")
    op.drop_column("entity_evidence", "retrieved_at")
