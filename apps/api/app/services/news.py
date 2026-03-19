"""Compatibility wrapper for news refresh service.

Canonical implementation lives in app.domains.news.services.refresh.
"""

from app.domains.news.services.refresh import (
    DEFAULT_NEWS_QUERIES,
    GOOGLE_NEWS_RSS_URL,
    PerplexityClient,
    _fetch_google_news_rss,
    refresh_news,
    settings,
)

__all__ = [
    "refresh_news",
    "_fetch_google_news_rss",
    "DEFAULT_NEWS_QUERIES",
    "GOOGLE_NEWS_RSS_URL",
    "settings",
    "PerplexityClient",
]
