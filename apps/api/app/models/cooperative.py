from datetime import datetime
from sqlalchemy import String, Text, Float, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
try:
    from pgvector.sqlalchemy import Vector
except Exception:  # pragma: no cover - fallback for test environments without pgvector
    # Lightweight fallback: represent vector column as a JSON/list of floats for tests
    def Vector(dim: int):
        return JSON
from app.db.session import Base
from app.models.common import TimestampMixin


class Cooperative(Base, TimestampMixin):
    __tablename__ = "cooperatives"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    altitude_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    varieties: Mapped[str | None] = mapped_column(String(255), nullable=True)
    certifications: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Workflow / CRM-ish fields
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="active"
    )  # active|watch|blocked|archived
    next_action: Mapped[str | None] = mapped_column(String(255), nullable=True)
    requested_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reliability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    economics_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    last_scored_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Peru Sourcing Intelligence fields (v0.4.0)
    operational_data: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # farmer_count, storage_capacity_kg, processing_facilities, years_exporting
    export_readiness: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # export_license, senasa_registered, certifications, customs_history, document_coordinator
    financial_data: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # annual_revenue_usd, export_volume_kg, fob_price_per_kg
    social_impact_data: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # projects, beneficiaries, etc.
    digital_footprint: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # website, social_media, photos, cupping_scores
    sourcing_scores: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # cached scoring results
    communication_metrics: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # avg_response_hours, languages, missed_meetings

    # Semantic search embedding (v0.5.0) – local sentence-transformers/all-MiniLM-L6-v2
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(384), nullable=True
    )  # 384 dims to match sentence-transformers/all-MiniLM-L6-v2
