from sqlalchemy import String, Float, Date, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class CoffeePriceHistory(Base, TimestampMixin):
    """Historical coffee price data for ML training."""

    __tablename__ = "coffee_price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    origin_country: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    origin_region: Mapped[str] = mapped_column(String(255), nullable=False)
    variety: Mapped[str] = mapped_column(String(255), nullable=False)
    process_method: Mapped[str] = mapped_column(String(255), nullable=False)
    quality_grade: Mapped[str] = mapped_column(String(255), nullable=False)
    cupping_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    certifications: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    price_usd_per_kg: Mapped[float] = mapped_column(Float, nullable=False)
    price_usd_per_lb: Mapped[float] = mapped_column(Float, nullable=False)
    ice_c_price_usd_per_lb: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Coffee C futures
    differential_usd_per_lb: Mapped[float] = mapped_column(Float, nullable=False)
    market_source: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # actual_trade, market_estimate, futures
