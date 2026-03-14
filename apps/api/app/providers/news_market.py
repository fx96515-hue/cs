"""News and market-intelligence provider catalog for PR721 integration."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx


def _provider_entry(
    *,
    name: str,
    group: str,
    mode: str,
    configured: bool,
    coverage: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "group": group,
        "mode": mode,
        "configured": configured,
        "coverage": coverage,
        "notes": notes,
    }


class NewsAPIProvider:
    SOURCE_NAME = "NewsAPI"
    BASE_URL = "https://newsapi.org/v2/everything"

    @staticmethod
    def provider_status() -> dict[str, Any]:
        return _provider_entry(
            name=NewsAPIProvider.SOURCE_NAME,
            group="news",
            mode="optional",
            configured=bool(os.getenv("NEWSAPI_KEY")),
            coverage="Global market news",
            notes="Optional structured news ingestion source.",
        )

    @staticmethod
    def fetch_coffee_news(api_key: str | None = None) -> list[dict[str, Any]]:
        key = api_key or os.getenv("NEWSAPI_KEY")
        if not key:
            return []

        response = httpx.get(
            NewsAPIProvider.BASE_URL,
            params={
                "q": "coffee market price Peru",
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 25,
                "apiKey": key,
            },
            timeout=15,
            headers={"User-Agent": "CoffeeStudio/1.0"},
        )
        response.raise_for_status()
        payload = response.json()
        return [
            {
                "title": article.get("title"),
                "source": article.get("source", {}).get("name"),
                "url": article.get("url"),
                "description": article.get("description"),
                "published_at": article.get("publishedAt"),
                "provider": NewsAPIProvider.SOURCE_NAME,
            }
            for article in payload.get("articles", [])
        ]


class TwitterSentimentProvider:
    SOURCE_NAME = "Twitter API"

    @staticmethod
    def provider_status() -> dict[str, Any]:
        return _provider_entry(
            name=TwitterSentimentProvider.SOURCE_NAME,
            group="sentiment",
            mode="optional",
            configured=bool(os.getenv("TWITTER_BEARER_TOKEN")),
            coverage="Public social sentiment",
            notes="Reserved for future social-signal ingestion.",
        )


class RedditSentimentProvider:
    SOURCE_NAME = "Reddit API"

    @staticmethod
    def provider_status() -> dict[str, Any]:
        return _provider_entry(
            name=RedditSentimentProvider.SOURCE_NAME,
            group="sentiment",
            mode="optional",
            configured=bool(os.getenv("REDDIT_CLIENT_ID")),
            coverage="Community sentiment",
            notes="Reserved for future community signal ingestion.",
        )


class WebIntelProvider:
    SOURCE_NAME = "Web Research"

    @staticmethod
    def provider_status() -> dict[str, Any]:
        return _provider_entry(
            name=WebIntelProvider.SOURCE_NAME,
            group="news",
            mode="active",
            configured=True,
            coverage="Existing in-product web intelligence",
            notes="Backed by the current news and enrichment flows.",
        )


class NewsProvider:
    @staticmethod
    def provider_catalog() -> list[dict[str, Any]]:
        return [
            NewsAPIProvider.provider_status(),
            TwitterSentimentProvider.provider_status(),
            RedditSentimentProvider.provider_status(),
            WebIntelProvider.provider_status(),
        ]

    @staticmethod
    def fetch_all_intelligence() -> dict[str, Any]:
        return {
            "news": NewsAPIProvider.fetch_coffee_news(),
            "providers": NewsProvider.provider_catalog(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def to_sentiment_record(sentiment_data: dict[str, Any]) -> dict[str, Any]:
        score = float(sentiment_data.get("sentiment_score", 0) or 0)
        if score > 0.2:
            label = "positive"
        elif score < -0.2:
            label = "negative"
        else:
            label = "neutral"

        return {
            "platform": sentiment_data.get("source", "unknown"),
            "sentiment_score": score,
            "sentiment_magnitude": abs(score),
            "sentiment_label": label,
            "entities": sentiment_data.get("entities") or [],
            "market_relevance_score": sentiment_data.get("market_relevance_score", 0.5),
            "price_signal": sentiment_data.get("price_signal", "neutral"),
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "published_at": sentiment_data.get("published_at")
            or datetime.now(timezone.utc).isoformat(),
        }
