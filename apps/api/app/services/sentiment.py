"""Compatibility wrapper for sentiment service.

Canonical implementation lives in app.domains.sentiment.services.analysis.
"""

from app.domains.sentiment.services.analysis import (
    aggregate_region_sentiment,
    analyze_news_items,
    analyze_text,
    get_entity_sentiment,
    get_region_sentiment,
)

__all__ = [
    "analyze_text",
    "analyze_news_items",
    "aggregate_region_sentiment",
    "get_region_sentiment",
    "get_entity_sentiment",
]
