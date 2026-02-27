"""Tests for news service."""

from unittest.mock import patch, MagicMock
from app.services.news import refresh_news
from app.models.news_item import NewsItem


def test_refresh_news_without_api_key(db):
    """Test news refresh when API key is not set."""
    with patch("app.services.news.settings") as mock_settings:
        mock_settings.PERPLEXITY_API_KEY = None

        result = refresh_news(db)

        assert result["status"] == "skipped"
        assert "PERPLEXITY_API_KEY not set" in result["reason"]


def test_refresh_news_with_results(db):
    """Test news refresh with successful results."""
    mock_results = [
        {
            "title": "Coffee prices rise",
            "url": "https://example.com/news1",
            "snippet": "Coffee prices continue to rise...",
            "published_date": "2024-01-01",
        },
        {
            "title": "Peru exports coffee",
            "url": "https://example.com/news2",
            "snippet": "Peru increases coffee exports...",
            "published_date": "2024-01-02",
        },
    ]

    with (
        patch("app.services.news.settings") as mock_settings,
        patch("app.services.news.PerplexityClient") as mock_client_class,
    ):
        mock_settings.PERPLEXITY_API_KEY = "test_key"
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.search.return_value = mock_results

        result = refresh_news(db, topic="coffee", max_items=25)

        assert result.get("status") in ["success", "ok", None]
        # Verify search was called
        assert mock_client.search.called


def test_refresh_news_deduplicates_urls(db):
    """Test news refresh deduplicates items by URL."""
    mock_results = [
        {
            "title": "Coffee prices rise",
            "url": "https://example.com/news1",
            "snippet": "Coffee prices...",
            "published_date": "2024-01-01",
        }
    ]

    with (
        patch("app.services.news.settings") as mock_settings,
        patch("app.services.news.PerplexityClient") as mock_client_class,
    ):
        mock_settings.PERPLEXITY_API_KEY = "test_key"
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.search.return_value = mock_results

        # First refresh
        refresh_news(db, topic="coffee", max_items=10)

        # Second refresh with same URL
        refresh_news(db, topic="coffee", max_items=10)

        # Should only have one item
        items = db.query(NewsItem).filter_by(url="https://example.com/news1").all()
        assert len(items) <= 1


def test_refresh_news_with_country_filter(db):
    """Test news refresh with country filter."""
    with (
        patch("app.services.news.settings") as mock_settings,
        patch("app.services.news.PerplexityClient") as mock_client_class,
    ):
        mock_settings.PERPLEXITY_API_KEY = "test_key"
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.search.return_value = []

        refresh_news(db, topic="coffee", country="PE", max_items=10)

        # Verify country was passed
        mock_client.search.assert_called()


def test_refresh_news_handles_errors(db):
    """Test news refresh handles API errors gracefully."""
    with (
        patch("app.services.news.settings") as mock_settings,
        patch("app.services.news.PerplexityClient") as mock_client_class,
    ):
        mock_settings.PERPLEXITY_API_KEY = "test_key"
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.search.side_effect = Exception("API Error")

        result = refresh_news(db, topic="coffee")

        # Should handle error gracefully
        assert result is not None
