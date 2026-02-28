"""Tests for sentiment analysis service and API routes."""

from datetime import datetime, timezone
from unittest.mock import patch

from app.models.news_item import NewsItem
from app.models.sentiment_score import SentimentScore
from app.services.sentiment import (
    analyze_news_items,
    analyze_text,
    aggregate_region_sentiment,
    get_region_sentiment,
    get_entity_sentiment,
)


# ---------------------------------------------------------------------------
# Unit tests – analyze_text
# ---------------------------------------------------------------------------


def test_analyze_text_positive():
    score, label = analyze_text("Coffee prices show strong growth and recovery")
    assert score > 0
    assert label == "positive"


def test_analyze_text_negative():
    score, label = analyze_text(
        "Crisis threatens coffee supply with drought and shortage"
    )
    assert score < 0
    assert label == "negative"


def test_analyze_text_neutral():
    score, label = analyze_text("The quick brown fox jumps over the lazy dog")
    assert score == 0.0
    assert label == "neutral"


def test_analyze_text_mixed():
    score, label = analyze_text("growth decline")
    # One positive, one negative ⇒ score == 0
    assert score == 0.0
    assert label == "neutral"


# ---------------------------------------------------------------------------
# Service tests – analyze_news_items
# ---------------------------------------------------------------------------


def test_analyze_news_items_scores_unscored(db):
    """Un-scored items should receive a sentiment_score."""
    item = NewsItem(
        topic="peru coffee",
        title="Strong growth in Peru coffee exports",
        url="https://example.com/sentiment-test-1",
        retrieved_at=datetime.now(timezone.utc),
    )
    db.add(item)
    db.commit()

    result = analyze_news_items(db)

    assert result["status"] == "ok"
    assert result["scored"] == 1
    db.refresh(item)
    assert item.sentiment_score is not None
    assert item.sentiment_label in ("positive", "negative", "neutral")


def test_analyze_news_items_skips_already_scored(db):
    """Already-scored items should not be re-processed."""
    item = NewsItem(
        topic="peru coffee",
        title="Old news",
        url="https://example.com/sentiment-test-2",
        retrieved_at=datetime.now(timezone.utc),
        sentiment_score=0.5,
        sentiment_label="positive",
    )
    db.add(item)
    db.commit()

    result = analyze_news_items(db)
    assert result["scored"] == 0


# ---------------------------------------------------------------------------
# Service tests – aggregate_region_sentiment
# ---------------------------------------------------------------------------


def test_aggregate_region_sentiment(db):
    items = [
        NewsItem(
            topic="peru coffee",
            title="Growth opportunity",
            url="https://example.com/s1",
            country="PE",
            retrieved_at=datetime.now(timezone.utc),
            sentiment_score=0.5,
            sentiment_label="positive",
        ),
        NewsItem(
            topic="peru coffee",
            title="Risk of drought",
            url="https://example.com/s2",
            country="PE",
            retrieved_at=datetime.now(timezone.utc),
            sentiment_score=-0.3,
            sentiment_label="negative",
        ),
    ]
    db.add_all(items)
    db.commit()

    result = aggregate_region_sentiment(db)

    assert result["status"] == "ok"
    assert "PE" in result["regions"]
    pe = result["regions"]["PE"]
    assert pe["article_count"] == 2
    # Average of 0.5 and -0.3 = 0.1 → positive (just barely)
    assert pe["score"] == 0.1


# ---------------------------------------------------------------------------
# Service tests – get_region_sentiment / get_entity_sentiment
# ---------------------------------------------------------------------------


def test_get_region_sentiment(db):
    now = datetime.now(timezone.utc)
    db.add(
        SentimentScore(
            region="PE",
            score=0.25,
            label="positive",
            article_count=5,
            scored_at=now,
        )
    )
    db.commit()

    data = get_region_sentiment(db, "PE")
    assert len(data) == 1
    assert data[0]["region"] == "PE"
    assert data[0]["score"] == 0.25


def test_get_entity_sentiment(db):
    now = datetime.now(timezone.utc)
    db.add(
        SentimentScore(
            entity_id=42,
            score=-0.1,
            label="negative",
            article_count=3,
            scored_at=now,
        )
    )
    db.commit()

    data = get_entity_sentiment(db, 42)
    assert len(data) == 1
    assert data[0]["entity_id"] == 42


# ---------------------------------------------------------------------------
# API route tests
# ---------------------------------------------------------------------------


def test_get_sentiment_region_empty(client, auth_headers, db):
    response = client.get("/sentiment/PE", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["region"] == "PE"
    assert body["total"] == 0


def test_get_sentiment_entity_empty(client, auth_headers, db):
    response = client.get("/sentiment/entity/1", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["entity_id"] == 1
    assert body["total"] == 0


def test_post_analyze_sentiment(client, auth_headers, db):
    item = NewsItem(
        topic="peru coffee",
        title="Strong growth in specialty coffee",
        url="https://example.com/analyze-test",
        retrieved_at=datetime.now(timezone.utc),
        country="PE",
    )
    db.add(item)
    db.commit()

    response = client.post("/sentiment/analyze", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["scored"] >= 1


def test_sentiment_requires_auth(client, db):
    response = client.get("/sentiment/PE")
    assert response.status_code == 401


def test_viewer_can_read_sentiment(client, viewer_auth_headers, db):
    response = client.get("/sentiment/PE", headers=viewer_auth_headers)
    assert response.status_code == 200


def test_viewer_cannot_analyze_sentiment(client, viewer_auth_headers, db):
    response = client.post("/sentiment/analyze", headers=viewer_auth_headers)
    assert response.status_code == 403


def test_sentiment_disabled_returns_503(client, auth_headers, db):
    with patch("app.api.routes.sentiment.settings") as mock_settings:
        mock_settings.SENTIMENT_ENABLED = False
        response = client.get("/sentiment/PE", headers=auth_headers)
        assert response.status_code == 503
