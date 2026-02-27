from sqlalchemy import String, Text, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class Region(Base, TimestampMixin):
    """Coffee producing regions with comprehensive sourcing intelligence data."""

    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    country: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # Description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Growing conditions
    elevation_min_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    elevation_max_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    soil_type: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Production data
    production_volume_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    production_share_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    harvest_months: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Quality profile
    typical_varieties: Mapped[str | None] = mapped_column(String(255), nullable=True)
    typical_processing: Mapped[str | None] = mapped_column(String(128), nullable=True)
    quality_profile: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Infrastructure and logistics
    main_port: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transport_time_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    logistics_cost_per_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    infrastructure_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Risk factors
    weather_risk: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )  # low/medium/high
    political_risk: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )  # low/medium/high
    logistics_risk: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )  # low/medium/high
    quality_consistency_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    __table_args__ = (
        UniqueConstraint("name", "country", name="uq_region_name_country"),
    )
