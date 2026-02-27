from datetime import date
from sqlalchemy import String, Float, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class FreightHistory(Base, TimestampMixin):
    """Historical freight data for ML training."""

    __tablename__ = "freight_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    route: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    origin_port: Mapped[str] = mapped_column(String(255), nullable=False)
    destination_port: Mapped[str] = mapped_column(String(255), nullable=False)
    carrier: Mapped[str] = mapped_column(String(255), nullable=False)
    container_type: Mapped[str] = mapped_column(String(16), nullable=False)
    weight_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    freight_cost_usd: Mapped[float] = mapped_column(Float, nullable=False)
    transit_days: Mapped[int] = mapped_column(Integer, nullable=False)
    departure_date: Mapped[date] = mapped_column(Date, nullable=False)
    arrival_date: Mapped[date] = mapped_column(Date, nullable=False)
    season: Mapped[str] = mapped_column(String(8), nullable=False)  # Q1, Q2, Q3, Q4
    fuel_price_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    port_congestion_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # 0-100
