from datetime import datetime
from sqlalchemy import String, Text, JSON, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
try:
    from pgvector.sqlalchemy import Vector
except Exception:  # pragma: no cover - fallback for test environments without pgvector
    def Vector(dim: int):
        return JSON

from app.db.session import Base
from app.models.common import TimestampMixin


class Roaster(Base, TimestampMixin):
    __tablename__ = "roasters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    peru_focus: Mapped[bool] = mapped_column(nullable=False, default=False)
    specialty_focus: Mapped[bool] = mapped_column(nullable=False, default=True)
    price_position: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # low|mid|premium|unknown
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional scoring / prioritization (can be used later)
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_scored_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="active"
    )  # active|watch|blocked|archived
    next_action: Mapped[str | None] = mapped_column(String(255), nullable=True)
    requested_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Semantic search embedding (v0.5.0) – local sentence-transformers/all-MiniLM-L6-v2
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(384), nullable=True
    )  # 384 dims to match sentence-transformers/all-MiniLM-L6-v2
