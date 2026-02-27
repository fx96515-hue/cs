"""Sentiment score time series per region and entity."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class SentimentScore(Base, TimestampMixin):
    """Aggregated sentiment score snapshot for a region or entity."""

    __tablename__ = "sentiment_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    region: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str] = mapped_column(String(16), nullable=False)
    article_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )


Index(
    "ix_sentiment_region_scored",
    SentimentScore.region,
    SentimentScore.scored_at,
)
Index(
    "ix_sentiment_entity_scored",
    SentimentScore.entity_id,
    SentimentScore.scored_at,
)
