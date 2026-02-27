from datetime import datetime
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class CuppingResult(Base, TimestampMixin):
    """Cupping result (SCA-style) for a lot/entity.

    This is not meant to fully replicate SCA forms, but to capture the key signals
    (score, descriptors, defects, notes) in a searchable form.
    """

    __tablename__ = "cupping_results"

    id: Mapped[int] = mapped_column(primary_key=True)

    occurred_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    taster: Mapped[str | None] = mapped_column(String(255), nullable=True)

    cooperative_id: Mapped[int | None] = mapped_column(
        ForeignKey("cooperatives.id"), nullable=True, index=True
    )
    lot_id: Mapped[int | None] = mapped_column(
        ForeignKey("lots.id"), nullable=True, index=True
    )
    roaster_id: Mapped[int | None] = mapped_column(
        ForeignKey("roasters.id"), nullable=True, index=True
    )

    sca_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    aroma: Mapped[float | None] = mapped_column(Float, nullable=True)
    flavor: Mapped[float | None] = mapped_column(Float, nullable=True)
    aftertaste: Mapped[float | None] = mapped_column(Float, nullable=True)
    acidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    body: Mapped[float | None] = mapped_column(Float, nullable=True)
    balance: Mapped[float | None] = mapped_column(Float, nullable=True)
    sweetness: Mapped[float | None] = mapped_column(Float, nullable=True)
    uniformity: Mapped[float | None] = mapped_column(Float, nullable=True)
    clean_cup: Mapped[float | None] = mapped_column(Float, nullable=True)

    descriptors: Mapped[str | None] = mapped_column(String(512), nullable=True)
    defects: Mapped[str | None] = mapped_column(String(512), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)


Index("ix_cupping_score", CuppingResult.sca_score)
