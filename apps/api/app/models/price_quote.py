from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.common import TimestampMixin


class PriceQuote(Base, TimestampMixin):
    """Price quote linked to a lot or deal with provenance."""

    __tablename__ = "price_quotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    lot_id: Mapped[int | None] = mapped_column(
        ForeignKey("lots.id"), nullable=True, index=True
    )
    deal_id: Mapped[int | None] = mapped_column(
        ForeignKey("deals.id"), nullable=True, index=True
    )
    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("sources.id"), nullable=True, index=True
    )

    price_per_kg: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    lot = relationship("Lot", lazy="joined")
    deal = relationship("Deal", lazy="joined")
    source = relationship("Source", lazy="joined")


Index("ix_price_quotes_lot_observed", PriceQuote.lot_id, PriceQuote.observed_at)
