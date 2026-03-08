from datetime import datetime

from sqlalchemy import String, Integer, DateTime, JSON, Index, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DataQualityFlag(Base):
    """Tracks data quality issues for entities and fields."""

    __tablename__ = "data_quality_flags"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    field_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    issue_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, default="info", index=True
    )  # info|warning|critical

    message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("sources.id"), nullable=True, index=True
    )
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)


Index(
    "ix_data_quality_flags_entity",
    DataQualityFlag.entity_type,
    DataQualityFlag.entity_id,
)
