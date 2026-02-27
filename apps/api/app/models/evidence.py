from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, JSON, UniqueConstraint, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class EntityEvidence(Base, TimestampMixin):
    """Stores provenance for an entity (cooperative/roaster) from external discovery.

    We keep it generic via entity_type + entity_id to avoid many join tables.
    """

    __tablename__ = "entity_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # cooperative|roaster
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    evidence_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Optional enrichment metadata
    retrieved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    extractor: Mapped[str | None] = mapped_column(String(64), nullable=True)
    snippet_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "entity_type", "entity_id", "evidence_url", name="uq_entity_evidence"
        ),
    )
