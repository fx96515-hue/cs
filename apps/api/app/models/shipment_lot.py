from sqlalchemy import Integer, ForeignKey, Float, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column
import sqlalchemy as sa

from app.db.session import Base


class ShipmentLot(Base):
    """Join table for many-to-many shipment <-> lot relationships."""

    __tablename__ = "shipment_lots"

    id: Mapped[int] = mapped_column(primary_key=True)
    shipment_id: Mapped[int] = mapped_column(
        ForeignKey("shipments.id"), nullable=False, index=True
    )
    lot_id: Mapped[int] = mapped_column(
        ForeignKey("lots.id"), nullable=False, index=True
    )
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[sa.DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("shipment_id", "lot_id", name="uq_shipment_lot"),
    )
