"""Sentiment analysis service for news items.

Provides keyword-based sentiment scoring with optional OpenAI fallback.
Scores range from -1.0 (very negative) to 1.0 (very positive).
Labels: "positive", "negative", "neutral".
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.news_item import NewsItem
from app.models.sentiment_score import SentimentScore

log = structlog.get_logger()

# --- keyword lexicons for lightweight sentiment ---
_POSITIVE_KEYWORDS = {
    "growth",
    "increase",
    "rise",
    "positive",
    "gain",
    "strong",
    "record",
    "boom",
    "expand",
    "improve",
    "recovery",
    "opportunity",
    "success",
    "surge",
    "high",
    "innovation",
    "sustainable",
    "premium",
    "award",
    "progress",
    "wachstum",
    "anstieg",
    "positiv",
    "erholung",
    "chance",
    "nachhaltig",
    "prämie",
}
_NEGATIVE_KEYWORDS = {
    "decline",
    "drop",
    "fall",
    "loss",
    "crisis",
    "risk",
    "drought",
    "flood",
    "shortage",
    "disruption",
    "delay",
    "threat",
    "concern",
    "weak",
    "low",
    "downturn",
    "collapse",
    "damage",
    "failure",
    "volatility",
    "rückgang",
    "krise",
    "risiko",
    "dürre",
    "mangel",
    "störung",
    "verlust",
    "schwach",
}


def _score_to_label(score: float) -> str:
    if score > 0.1:
        return "positive"
    if score < -0.1:
        return "negative"
    return "neutral"


def analyze_text(text: str) -> tuple[float, str]:
    """Compute sentiment for a single text using keyword matching.

    Args:
        text: Input text (title + snippet).

    Returns:
        (score, label) tuple.
    """
    words = set(text.lower().split())
    pos = len(words & _POSITIVE_KEYWORDS)
    neg = len(words & _NEGATIVE_KEYWORDS)
    total = pos + neg
    if total == 0:
        return 0.0, "neutral"
    score = round((pos - neg) / total, 4)
    return score, _score_to_label(score)


def analyze_news_items(db: Session, *, batch_size: int = 200) -> dict[str, Any]:
    """Score all un-scored news items and persist results.

    Args:
        db: Database session
        batch_size: Max items to process in one call

    Returns:
        Summary dict with counts
    """
    items = (
        db.query(NewsItem)
        .filter(NewsItem.sentiment_score.is_(None))
        .limit(batch_size)
        .all()
    )

    scored = 0
    for item in items:
        text = f"{item.title or ''} {item.snippet or ''}"
        score, label = analyze_text(text)
        item.sentiment_score = score
        item.sentiment_label = label
        scored += 1

    if scored:
        db.commit()

    log.info("sentiment_analysis_complete", scored=scored)
    return {"status": "ok", "scored": scored}


def aggregate_region_sentiment(db: Session) -> dict[str, Any]:
    """Aggregate per-region sentiment from scored news items and store snapshots.

    Regions are derived from the ``country`` column of news items.

    Returns:
        Summary dict with region scores
    """
    from sqlalchemy import func

    now = datetime.now(timezone.utc)
    rows = (
        db.query(
            NewsItem.country,
            func.avg(NewsItem.sentiment_score),
            func.count(NewsItem.id),
        )
        .filter(NewsItem.sentiment_score.isnot(None))
        .group_by(NewsItem.country)
        .all()
    )

    regions: dict[str, dict] = {}
    for country, avg_score, count in rows:
        region_key = country or "global"
        avg_score = round(float(avg_score), 4)
        label = _score_to_label(avg_score)

        snapshot = SentimentScore(
            region=region_key,
            score=avg_score,
            label=label,
            article_count=int(count),
            scored_at=now,
        )
        db.add(snapshot)
        regions[region_key] = {
            "score": avg_score,
            "label": label,
            "article_count": int(count),
        }

    if regions:
        db.commit()

    log.info("region_sentiment_aggregated", regions=list(regions.keys()))
    return {"status": "ok", "regions": regions}


def get_region_sentiment(
    db: Session, region: str, *, limit: int = 90
) -> list[dict[str, Any]]:
    """Return sentiment time series for a region.

    Args:
        db: Database session
        region: Region/country code
        limit: Max number of data points

    Returns:
        List of score dicts ordered by time
    """
    rows = (
        db.query(SentimentScore)
        .filter(SentimentScore.region == region)
        .order_by(SentimentScore.scored_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "region": r.region,
            "score": r.score,
            "label": r.label,
            "article_count": r.article_count,
            "scored_at": r.scored_at.isoformat() if r.scored_at else None,
        }
        for r in reversed(rows)
    ]


def get_entity_sentiment(
    db: Session, entity_id: int, *, limit: int = 90
) -> list[dict[str, Any]]:
    """Return sentiment time series for a specific entity.

    Args:
        db: Database session
        entity_id: Entity identifier
        limit: Max number of data points

    Returns:
        List of score dicts ordered by time
    """
    rows = (
        db.query(SentimentScore)
        .filter(SentimentScore.entity_id == entity_id)
        .order_by(SentimentScore.scored_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "entity_id": r.entity_id,
            "score": r.score,
            "label": r.label,
            "article_count": r.article_count,
            "scored_at": r.scored_at.isoformat() if r.scored_at else None,
        }
        for r in reversed(rows)
    ]
