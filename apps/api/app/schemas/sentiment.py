"""Compatibility wrapper for sentiment schemas.

Canonical implementation lives in app.domains.sentiment.schemas.sentiment.
"""

from app.domains.sentiment.schemas.sentiment import (
    SentimentAnalyzeResponse,
    SentimentScoreOut,
    SentimentTimeSeriesResponse,
)

__all__ = [
    "SentimentScoreOut",
    "SentimentTimeSeriesResponse",
    "SentimentAnalyzeResponse",
]