from sqlalchemy import String, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class PeruRegion(Base, TimestampMixin):
    """Knowledge Base for Peru coffee regions (explanations, risks, logistics)."""

    __tablename__ = "peru_regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_de: Mapped[str | None] = mapped_column(Text, nullable=True)

    typical_varieties: Mapped[str | None] = mapped_column(Text, nullable=True)
    typical_processing: Mapped[str | None] = mapped_column(Text, nullable=True)
    altitude_range: Mapped[str | None] = mapped_column(String(64), nullable=True)

    logistics_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sources: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (UniqueConstraint("code", name="uq_peru_region_code"),)
