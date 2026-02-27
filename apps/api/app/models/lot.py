from sqlalchemy import String, Text, Float, JSON, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class Lot(Base, TimestampMixin):
    """A tradable coffee lot (usually from a cooperative), used for margin calculations."""

    __tablename__ = "lots"

    id: Mapped[int] = mapped_column(primary_key=True)
    cooperative_id: Mapped[int] = mapped_column(
        ForeignKey("cooperatives.id"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    crop_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    incoterm: Mapped[str | None] = mapped_column(
        String(16), nullable=True
    )  # FOB|CIF|...

    price_per_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)

    expected_cupping_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    varieties: Mapped[str | None] = mapped_column(String(255), nullable=True)
    processing: Mapped[str | None] = mapped_column(String(64), nullable=True)

    availability_window: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)


Index("ix_lots_coop_name", Lot.cooperative_id, Lot.name)
