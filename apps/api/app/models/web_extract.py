from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class WebExtract(Base, TimestampMixin):
    """Stores raw web text extraction + structured JSON extraction.

    This is the backbone for entity verification and deep research.
    """

    __tablename__ = "web_extracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="ok"
    )  # ok|failed

    retrieved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lang: Mapped[str | None] = mapped_column(String(16), nullable=True)

    extracted_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    translated_de: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "url", name="uq_web_extract"),
    )


Index("ix_web_extracts_entity_type_id", WebExtract.entity_type, WebExtract.entity_id)
