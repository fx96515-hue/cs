from sqlalchemy import String, Float, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from app.models.common import TimestampMixin


class Shipment(Base, TimestampMixin):
    """Shipment tracking for coffee lots from origin to destination."""

    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(primary_key=True)
    lot_id: Mapped[int | None] = mapped_column(
        ForeignKey("lots.id"), nullable=True, index=True
    )
    cooperative_id: Mapped[int | None] = mapped_column(
        ForeignKey("cooperatives.id"), nullable=True, index=True
    )
    roaster_id: Mapped[int | None] = mapped_column(
        ForeignKey("roasters.id"), nullable=True, index=True
    )

    # Shipment details
    container_number: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    bill_of_lading: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    container_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Route
    origin_port: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_port: Mapped[str] = mapped_column(String(100), nullable=False)
    current_location: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Dates
    departure_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estimated_arrival: Mapped[str | None] = mapped_column(String(50), nullable=True)
    actual_arrival: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default="in_transit", nullable=False
    )
    status_updated_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    delay_hours: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Tracking
    tracking_events: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)

    # Metadata
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
