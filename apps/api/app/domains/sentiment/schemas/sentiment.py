"""Pydantic schemas for the sentiment API."""

from datetime import datetime
from pydantic import BaseModel


class SentimentScoreOut(BaseModel):
    id: int
    region: str | None = None
    entity_id: int | None = None
    score: float
    label: str
    article_count: int = 0
    scored_at: datetime | None = None

    class Config:
        from_attributes = True


class SentimentTimeSeriesResponse(BaseModel):
    region: str | None = None
    entity_id: int | None = None
    data: list[SentimentScoreOut]
    total: int


class SentimentAnalyzeResponse(BaseModel):
    status: str
    scored: int = 0
    regions: dict | None = None
