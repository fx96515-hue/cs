"""Sentiment analysis API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.core.config import settings
from app.domains.sentiment.schemas.sentiment import (
    SentimentAnalyzeResponse,
    SentimentScoreOut,
    SentimentTimeSeriesResponse,
)
from app.domains.sentiment.services.analysis import (
    analyze_news_items,
    aggregate_region_sentiment,
    get_entity_sentiment,
    get_region_sentiment,
)

router = APIRouter()
DbSessionDep = Annotated[Session, Depends(get_db)]
ViewerPermissionDep = Annotated[
    None, Depends(require_role("admin", "analyst", "viewer"))
]
AnalystPermissionDep = Annotated[None, Depends(require_role("admin", "analyst"))]


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
    db: DbSessionDep,
    _: ViewerPermissionDep,
    limit: Annotated[int, Query(ge=1, le=365)] = 90,
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
    entity_id: Annotated[int, Path(ge=1)],
    db: DbSessionDep,
    _: ViewerPermissionDep,
    limit: Annotated[int, Query(ge=1, le=365)] = 90,
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
    db: DbSessionDep,
    _: AnalystPermissionDep,
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
