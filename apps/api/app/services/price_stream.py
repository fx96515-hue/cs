"""Redis Pub/Sub price stream service.

Publishes Coffee C futures prices to a Redis channel so that WebSocket
clients receive near-realtime updates without polling the upstream API
on every connection.

Redis layout
------------
* Cache key  ``coffee:price:latest``   – JSON blob, TTL = 120 s
* Pub/Sub channel ``coffee:price:stream`` – same JSON blob on each update
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

import redis
import structlog

from app.providers.coffee_prices import CoffeeQuote

log = structlog.get_logger()

REDIS_CACHE_KEY = "coffee:price:latest"
REDIS_CHANNEL = "coffee:price:stream"
CACHE_TTL_SECONDS = 120  # price is considered live if < 2 min old


def _quote_to_dict(quote: CoffeeQuote) -> dict:
    """Serialise a CoffeeQuote to a JSON-safe dict."""
    return {
        "price_usd_per_lb": quote.price_usd_per_lb,
        "observed_at": quote.observed_at.isoformat(),
        "source_name": quote.source_name,
        "metadata": quote.metadata,
    }


def publish_price(redis_client: redis.Redis, quote: CoffeeQuote) -> None:
    """Persist *quote* in the Redis cache and broadcast it on the Pub/Sub channel.

    Args:
        redis_client: Active Redis connection.
        quote: Latest coffee price quote.
    """
    payload = json.dumps(_quote_to_dict(quote))
    try:
        redis_client.set(REDIS_CACHE_KEY, payload, ex=CACHE_TTL_SECONDS)
        redis_client.publish(REDIS_CHANNEL, payload)
        log.info(
            "price_stream_published",
            price=quote.price_usd_per_lb,
            source=quote.source_name,
        )
    except Exception as e:
        log.error("price_stream_publish_failed", error=str(e), exc_info=True)


def get_cached_price(redis_client: redis.Redis) -> Optional[dict]:
    """Return the last cached price dict, or *None* if the cache is empty/expired.

    Args:
        redis_client: Active Redis connection.

    Returns:
        Dict with ``price_usd_per_lb``, ``observed_at``, ``source_name``,
        ``metadata``; or *None*.
    """
    try:
        raw = redis_client.get(REDIS_CACHE_KEY)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            text = raw.decode("utf-8")
        elif isinstance(raw, str):
            text = raw
        else:
            log.warning(
                "price_stream_cache_unexpected_type",
                type=str(type(raw)),
            )
            return None
        return json.loads(text)
    except Exception as e:
        log.warning("price_stream_cache_read_failed", error=str(e))
        return None


def fetch_and_publish(
    redis_client: redis.Redis,
    api_key: Optional[str] = None,
) -> Optional[dict]:
    """Fetch a fresh price and publish it to Redis.

    Convenience helper used by the Celery beat task and the circuit-breaker
    wired orchestrator.

    Args:
        redis_client: Active Redis connection.
        api_key: Twelve Data API key (optional – falls back to Yahoo Finance).

    Returns:
        The published price dict, or *None* on failure.
    """
    from app.providers.ice_realtime import fetch_realtime_coffee_price

    quote = fetch_realtime_coffee_price(api_key=api_key)
    if quote is None:
        log.warning("fetch_and_publish_no_quote")
        return None

    publish_price(redis_client, quote)
    return _quote_to_dict(quote)
