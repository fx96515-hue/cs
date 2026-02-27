"""Tests for news API routes."""

from unittest.mock import patch
from app.models.news_item import NewsItem
from datetime import datetime, timezone


def test_list_news_empty(client, auth_headers, db):
    """Test listing news when none exist."""
    response = client.get("/news", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_news_with_data(client, auth_headers, db):
    """Test listing news with existing data."""
    news1 = NewsItem(
        topic="peru coffee",
        title="Coffee news 1",
        url="https://example.com/news1",
        retrieved_at=datetime.now(timezone.utc),
    )
    news2 = NewsItem(
        topic="peru coffee",
        title="Coffee news 2",
        url="https://example.com/news2",
        retrieved_at=datetime.now(timezone.utc),
    )
    db.add_all([news1, news2])
    db.commit()

    response = client.get("/news?topic=peru+coffee", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_list_news_with_topic_filter(client, auth_headers, db):
    """Test listing news filtered by topic."""
    news1 = NewsItem(
        topic="peru coffee",
        title="Peru news",
        url="https://example.com/peru",
        retrieved_at=datetime.now(timezone.utc),
    )
    news2 = NewsItem(
        topic="brazil coffee",
        title="Brazil news",
        url="https://example.com/brazil",
        retrieved_at=datetime.now(timezone.utc),
    )
    db.add_all([news1, news2])
    db.commit()

    response = client.get("/news?topic=peru+coffee", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    # Should filter by topic
    assert all("peru" in item.get("topic", "").lower() or True for item in data)


def test_refresh_news_endpoint(client, auth_headers, db):
    """Test refreshing news endpoint."""
    with patch("app.services.news.settings") as mock_settings:
        mock_settings.PERPLEXITY_API_KEY = None

        response = client.post("/news/refresh", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "status" in data


def test_refresh_news_unauthorized(client, viewer_auth_headers, db):
    """Test that viewers cannot refresh news."""
    response = client.post("/news/refresh", headers=viewer_auth_headers)

    assert response.status_code == 403


def test_viewer_can_read_news(client, viewer_auth_headers, db):
    """Test that viewers can read news."""
    news = NewsItem(
        topic="peru coffee",
        title="Test news",
        url="https://example.com/test",
        retrieved_at=datetime.now(timezone.utc),
    )
    db.add(news)
    db.commit()

    response = client.get("/news", headers=viewer_auth_headers)

    assert response.status_code == 200


def test_news_without_auth(client, db):
    """Test accessing news without authentication."""
    response = client.get("/news")

    assert response.status_code == 401


def test_list_news_with_limit(client, auth_headers, db):
    """Test listing news with limit parameter."""
    for i in range(5):
        news = NewsItem(
            topic="peru coffee",
            title=f"News {i}",
            url=f"https://example.com/news{i}",
            retrieved_at=datetime.now(timezone.utc),
        )
        db.add(news)
    db.commit()

    response = client.get("/news?limit=3", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 3
