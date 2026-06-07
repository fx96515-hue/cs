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


def _already_seen(url: str | None, stored_urls: set[str]) -> bool:
    if not url or url in stored_urls:
        return True
    stored_urls.add(url)
    return False


def _refresh_from_perplexity(
    db: Session,
    *,
    topic: str,
    country: str | None,
    max_items: int,
    now: datetime,
    stored_urls: set[str],
) -> tuple[int, int, list[str], bool]:
    created = 0
    updated = 0
    errors: list[str] = []
    provider_used = False
    client = PerplexityClient()

    try:
        queries = [f"{topic} {query_suffix}" for query_suffix in DEFAULT_NEWS_QUERIES]
        for query_text in queries:
            if created + updated >= max_items:
                break
            try:
                raw_results = client.search(
                    query_text,
                    max_results=min(10, max_items),
                    country=country or "DE",
                    max_tokens_per_page=384,
                )
                results = [
                    {
                        "title": _coerce_result_field(item, "title"),
                        "url": _coerce_result_field(item, "url"),
                        "snippet": _coerce_result_field(item, "snippet"),
                        "published_at": _coerce_result_field(item, "published_date"),
                    }
                    for item in raw_results
                    if not _already_seen(_coerce_result_field(item, "url"), stored_urls)
                ]
                c, u = _upsert_news_items(
                    db,
                    topic=topic,
                    country=country,
                    provider="perplexity",
                    query=query_text,
                    results=results,
                    max_items=max_items - (created + updated),
                    now=now,
                )
                created += c
                updated += u
            except Exception:
                db.rollback()
                errors.append(f"perplexity query failed: {query_text}")

        provider_used = bool(created or updated)
        return created, updated, errors, provider_used
    finally:
        client.close()


def _refresh_from_google_rss(
    db: Session,
    *,
    topic: str,
    country: str | None,
    max_items: int,
    now: datetime,
    already_created: int,
    already_updated: int,
    stored_urls: set[str],
) -> tuple[int, int, list[str], bool]:
    remaining = max_items - (already_created + already_updated)
    if remaining <= 0:
        return 0, 0, [], False

    try:
        query = quote_plus(topic)
        rss_results = [
            item
            for item in _fetch_google_news_rss(
                topic,
                country=country,
                max_items=max_items,
            )
            if not _already_seen(item.get("url"), stored_urls)
        ]
        created, updated = _upsert_news_items(
            db,
            topic=topic,
            country=country,
            provider="google_news_rss",
            query=query,
            results=rss_results,
            max_items=remaining,
            now=now,
        )
        return created, updated, [], bool(created or updated)
    except Exception:
        db.rollback()
        return 0, 0, ["google_news_rss failed"], False


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

    if settings.PERPLEXITY_API_KEY:
        providers_attempted.append("perplexity")
        p_created, p_updated, p_errors, p_used = _refresh_from_perplexity(
            db,
            topic=topic,
            country=country,
            max_items=max_items,
            now=now,
            stored_urls=stored_urls,
        )
        created += p_created
        updated += p_updated
        errors.extend(p_errors)
        if p_used:
            provider_used = "perplexity"
    else:
        errors.append("perplexity unavailable: PERPLEXITY_API_KEY not set")

    if created + updated < max_items:
        providers_attempted.append("google_news_rss")
        r_created, r_updated, r_errors, r_used = _refresh_from_google_rss(
            db,
            topic=topic,
            country=country,
            max_items=max_items,
            now=now,
            already_created=created,
            already_updated=updated,
            stored_urls=stored_urls,
        )
        created += r_created
        updated += r_updated
        errors.extend(r_errors)
        if r_used and provider_used is None:
            provider_used = "google_news_rss"

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
