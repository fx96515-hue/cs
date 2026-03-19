"""Compatibility wrapper for news schemas.

Canonical implementation lives in app.domains.news.schemas.news.
"""

from app.domains.news.schemas.news import NewsItemOut, NewsRefreshResponse

__all__ = ["NewsItemOut", "NewsRefreshResponse"]
