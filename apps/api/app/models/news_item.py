from datetime import datetime
from sqlalchemy import String, Text, Float, DateTime, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class NewsItem(Base, TimestampMixin):
    """A single news/search item persisted for the Market Radar."""

    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)

    country: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    retrieved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # Sentiment analysis results
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_label: Mapped[str | None] = mapped_column(
        String(16), nullable=True, index=True
    )

    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (UniqueConstraint("url", name="uq_news_url"),)


Index("ix_news_topic_retrieved", NewsItem.topic, NewsItem.retrieved_at)
