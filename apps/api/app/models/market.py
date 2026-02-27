from datetime import datetime
from sqlalchemy import String, Text, Float, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class MarketObservation(Base, TimestampMixin):
    """A market observation (FX, coffee price, freight, etc.) with provenance."""

    __tablename__ = "market_observations"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Example keys: FX:USD_EUR, COFFEE_C:USD_LB, FREIGHT:USD_PER_40FT
    key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)

    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )

    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("sources.id"), nullable=True, index=True
    )

    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)


Index(
    "ix_market_observations_key_observed_at",
    MarketObservation.key,
    MarketObservation.observed_at,
)
