from datetime import datetime
from sqlalchemy import String, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class MarginRun(Base, TimestampMixin):
    """Stores ..."""

    __tablename__ = "margin_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    lot_id: Mapped[int] = mapped_column(
        ForeignKey("lots.id"), nullable=False, index=True
    )
    profile: Mapped[str] = mapped_column(
        String(64), nullable=False, default="conservative"
    )
    inputs: Mapped[dict] = mapped_column(JSON, nullable=False)
    outputs: Mapped[dict] = mapped_column(JSON, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )


Index("ix_margin_runs_lot_profile", MarginRun.lot_id, MarginRun.profile)
