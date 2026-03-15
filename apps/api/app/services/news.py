from __future__ import annotations

from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus
from xml.etree import ElementTree as ET

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.news_item import NewsItem
from app.providers.perplexity import PerplexityClient


DEFAULT_NEWS_QUERIES: list[str] = [
    "Peru coffee news export",
    "Peru specialty coffee cooperative export",
    "Arabica coffee price news",
    "shipping disruption coffee beans",
]

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"


def _coerce_result_field(result: Any, field: str) -> Any:
    if isinstance(result, dict):
        return result.get(field)
    return getattr(result, field, None)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        try:
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            return None


def _upsert_news_items(
    db: Session,
    *,
    topic: str,
    country: str | None,
    provider: str,
    query: str,
    results: list[dict[str, Any]],
    max_items: int,
    now: datetime,
) -> tuple[int, int]:
    created = 0
    updated = 0
    processed = 0

    for result in results:
        if processed >= max_items:
            break

        url = _coerce_result_field(result, "url")
        if not url:
            continue

        stmt = select(NewsItem).where(NewsItem.url == url)
        item = db.scalar(stmt)
        if not item:
            item = NewsItem(
                topic=topic,
                title=_coerce_result_field(result, "title") or url,
                url=url,
            )
            db.add(item)
            created += 1
        else:
            updated += 1

        item.title = str(_coerce_result_field(result, "title") or item.title)[:500]
        item.snippet = _coerce_result_field(result, "snippet") or item.snippet
        item.country = country
        item.published_at = _parse_datetime(
            _coerce_result_field(result, "published_at")
        )
        item.retrieved_at = now
        item.meta = {"provider": provider, "query": query}
        processed += 1

    if processed:
        db.commit()
    return created, updated


def _fetch_google_news_rss(
    topic: str,
    *,
    country: str | None,
    max_items: int,
) -> list[dict[str, Any]]:
    params = {
        "q": f"{topic} when:30d",
        "hl": "en-US",
        "gl": country or "US",
        "ceid": f"{country or 'US'}:en",
    }
    response = httpx.get(
        GOOGLE_NEWS_RSS_URL,
        params=params,
        timeout=20.0,
        follow_redirects=True,
        headers={"User-Agent": "CoffeeStudio/1.0"},
    )
    response.raise_for_status()

    root = ET.fromstring(response.text)
    items: list[dict[str, Any]] = []
    for item in root.findall("./channel/item"):
        link = item.findtext("link")
        title = item.findtext("title")
        description = item.findtext("description")
        pub_date = item.findtext("pubDate")

        if not link:
            continue

        items.append(
            {
                "title": title or link,
                "url": link,
                "snippet": description,
                "published_at": pub_date,
            }
        )
        if len(items) >= max_items:
            break

    return items


def refresh_news(
    db: Session,
    *,
    topic: str = "coffee",
    country: str | None = None,
    max_items: int = 25,
) -> dict[str, Any]:
    """Refresh Market Radar news using Perplexity first and RSS fallback."""

    now = datetime.now(timezone.utc)
    created = 0
    updated = 0
    errors: list[str] = []
    providers_attempted: list[str] = []
    provider_used: str | None = None
    stored_urls: set[str] = set()

    def _sanitize_error(message: str) -> str:
        # Keep client-facing errors generic; full exception details stay in server logs.
        return message

    def _already_seen(url: str | None) -> bool:
        if not url or url in stored_urls:
            return True
        stored_urls.add(url)
        return False

    if settings.PERPLEXITY_API_KEY:
        client = PerplexityClient()
        try:
            queries = [f"{topic} {q}" for q in DEFAULT_NEWS_QUERIES]
            providers_attempted.append("perplexity")

            for q in queries:
                if created + updated >= max_items:
                    break
                try:
                    raw_results = client.search(
                        q,
                        max_results=min(10, max_items),
                        country=country or "DE",
                        max_tokens_per_page=384,
                    )
                    results = [
                        {
                            "title": _coerce_result_field(item, "title"),
                            "url": _coerce_result_field(item, "url"),
                            "snippet": _coerce_result_field(item, "snippet"),
                            "published_at": _coerce_result_field(
                                item, "published_date"
                            ),
                        }
                        for item in raw_results
                        if not _already_seen(_coerce_result_field(item, "url"))
                    ]
                    c, u = _upsert_news_items(
                        db,
                        topic=topic,
                        country=country,
                        provider="perplexity",
                        query=q,
                        results=results,
                        max_items=max_items - (created + updated),
                        now=now,
                    )
                    created += c
                    updated += u
                except Exception:
                    db.rollback()
                    errors.append(_sanitize_error(f"perplexity query failed: {q}"))

            if created or updated:
                provider_used = "perplexity"
        finally:
            client.close()
    else:
        errors.append("perplexity unavailable: PERPLEXITY_API_KEY not set")

    if created + updated < max_items:
        try:
            providers_attempted.append("google_news_rss")
            query = quote_plus(topic)
            rss_results = [
                item
                for item in _fetch_google_news_rss(
                    topic,
                    country=country,
                    max_items=max_items,
                )
                if not _already_seen(item.get("url"))
            ]
            c, u = _upsert_news_items(
                db,
                topic=topic,
                country=country,
                provider="google_news_rss",
                query=query,
                results=rss_results,
                max_items=max_items - (created + updated),
                now=now,
            )
            created += c
            updated += u
            if (c or u) and provider_used is None:
                provider_used = "google_news_rss"
        except Exception:
            db.rollback()
            errors.append(_sanitize_error("google_news_rss failed"))

    status = "ok" if (created or updated) else "failed"
    return {
        "status": status,
        "topic": topic,
        "created": created,
        "updated": updated,
        "errors": errors,
        "providers_attempted": providers_attempted,
        "provider_used": provider_used,
    }
