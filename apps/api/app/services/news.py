from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.models.news_item import NewsItem
from app.providers.perplexity import PerplexityClient


DEFAULT_NEWS_QUERIES: list[str] = [
    "Peru coffee news export",
    "Peru specialty coffee cooperative export",
    "Arabica coffee price news",
    "shipping disruption coffee beans",
]


def refresh_news(
    db: Session,
    *,
    topic: str = "coffee",
    country: str | None = None,
    max_items: int = 25,
) -> dict[str, Any]:
    """Refresh Market Radar news using Perplexity Search.

    Stores items by URL (idempotent). If PERPLEXITY_API_KEY is missing, returns a fail-fast error.
    """
    if not settings.PERPLEXITY_API_KEY:
        return {"status": "skipped", "reason": "PERPLEXITY_API_KEY not set"}

    now = datetime.now(timezone.utc)
    client = PerplexityClient()
    created = 0
    updated = 0
    errors: list[str] = []

    try:
        queries = [f"{topic} {q}" for q in DEFAULT_NEWS_QUERIES]
        seen: set[str] = set()

        for q in queries:
            try:
                results = client.search(
                    q, max_results=10, country=country or "DE", max_tokens_per_page=384
                )
                for r in results:
                    if not r.url or r.url in seen:
                        continue
                    seen.add(r.url)
                    stmt = select(NewsItem).where(NewsItem.url == r.url)
                    item = db.scalar(stmt)
                    if not item:
                        item = NewsItem(topic=topic, title=r.title or r.url, url=r.url)
                        db.add(item)
                        created += 1
                    else:
                        updated += 1
                    item.title = (r.title or item.title)[:500]
                    item.snippet = r.snippet or item.snippet
                    item.country = country
                    item.retrieved_at = now
                    item.meta = {"provider": "perplexity", "query": q}
                    db.commit()
            except Exception as e:
                db.rollback()
                errors.append(f"query failed: {q}: {e}")

        return {
            "status": "ok",
            "topic": topic,
            "created": created,
            "updated": updated,
            "errors": errors,
        }
    finally:
        client.close()
