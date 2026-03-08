from datetime import datetime

from sqlalchemy import String, Integer, DateTime, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class EntityVersion(Base):
    """Immutable snapshot of an entity state for versioning/audit."""

    __tablename__ = "entity_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    changed_by: Mapped[str | None] = mapped_column(String(320), nullable=True)
    change_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "entity_type", "entity_id", "version", name="uq_entity_version"
        ),
    )


Index("ix_entity_versions_entity", EntityVersion.entity_type, EntityVersion.entity_id)
