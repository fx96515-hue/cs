from datetime import datetime
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.common import TimestampMixin, SoftDeleteMixin


class Deal(Base, TimestampMixin, SoftDeleteMixin):
    """Commercial deal for a lot/cooperative/roaster."""

    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(primary_key=True)
    cooperative_id: Mapped[int | None] = mapped_column(
        ForeignKey("cooperatives.id"), nullable=True, index=True
    )
    roaster_id: Mapped[int | None] = mapped_column(
        ForeignKey("roasters.id"), nullable=True, index=True
    )
    lot_id: Mapped[int | None] = mapped_column(
        ForeignKey("lots.id"), nullable=True, index=True
    )

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="open", index=True
    )  # open|in_progress|closed|canceled
    incoterm: Mapped[str | None] = mapped_column(String(16), nullable=True)

    price_per_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_eur: Mapped[float | None] = mapped_column(Float, nullable=True)

    origin_country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    origin_region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    variety: Mapped[str | None] = mapped_column(String(128), nullable=True)
    process_method: Mapped[str | None] = mapped_column(String(128), nullable=True)
    quality_grade: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cupping_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    certifications: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    cooperative = relationship("Cooperative", lazy="joined")
    roaster = relationship("Roaster", lazy="joined")
    lot = relationship("Lot", lazy="joined")


Index("ix_deals_status_closed_at", Deal.status, Deal.closed_at)
