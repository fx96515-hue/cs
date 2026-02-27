"""Sentiment analysis API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.core.config import settings
from app.schemas.sentiment import (
    SentimentAnalyzeResponse,
    SentimentScoreOut,
    SentimentTimeSeriesResponse,
)
from app.services.sentiment import (
    analyze_news_items,
    aggregate_region_sentiment,
    get_entity_sentiment,
    get_region_sentiment,
)

router = APIRouter()


def _require_sentiment_enabled() -> None:
    """Raise 503 when the sentiment feature flag is off."""
    if not getattr(settings, "SENTIMENT_ENABLED", False):
        raise HTTPException(
            status_code=503,
            detail="Sentiment analysis is disabled (SENTIMENT_ENABLED=false).",
        )


@router.get("/{region}", response_model=SentimentTimeSeriesResponse)
def sentiment_by_region(
    region: str,
    limit: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Return sentiment time series for a region."""
    _require_sentiment_enabled()
    data = get_region_sentiment(db, region, limit=limit)
    return SentimentTimeSeriesResponse(
        region=region,
        data=[SentimentScoreOut(**d) for d in data],
        total=len(data),
    )


@router.get("/entity/{entity_id}", response_model=SentimentTimeSeriesResponse)
def sentiment_by_entity(
    entity_id: int,
    limit: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Return sentiment time series for a specific entity."""
    _require_sentiment_enabled()
    data = get_entity_sentiment(db, entity_id, limit=limit)
    return SentimentTimeSeriesResponse(
        entity_id=entity_id,
        data=[SentimentScoreOut(**d) for d in data],
        total=len(data),
    )


@router.post("/analyze", response_model=SentimentAnalyzeResponse)
def run_sentiment_analysis(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    """Manually trigger sentiment analysis on unscored news items."""
    _require_sentiment_enabled()
    result = analyze_news_items(db)
    agg = aggregate_region_sentiment(db)
    return SentimentAnalyzeResponse(
        status=result["status"],
        scored=result["scored"],
        regions=agg.get("regions"),
    )
