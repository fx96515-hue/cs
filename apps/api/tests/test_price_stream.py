"""Tests for the Redis price stream service."""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.providers.coffee_prices import CoffeeQuote
from app.services.price_stream import (
    CACHE_TTL_SECONDS,
    REDIS_CACHE_KEY,
    REDIS_CHANNEL,
    get_cached_price,
    publish_price,
)


def _make_quote(price: float = 2.40) -> CoffeeQuote:
    return CoffeeQuote(
        price_usd_per_lb=price,
        observed_at=datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        source_name="Twelve Data (ICE KC1!)",
        source_url="https://api.twelvedata.com/price",
        raw_data="{}",
        metadata={"provider": "twelve_data"},
    )


class TestPublishPrice:
    def test_sets_cache_and_publishes(self):
        redis_mock = MagicMock()
        quote = _make_quote(2.45)

        publish_price(redis_mock, quote)

        # Should set the cache key with TTL
        redis_mock.set.assert_called_once()
        call_args = redis_mock.set.call_args
        assert call_args[0][0] == REDIS_CACHE_KEY
        payload = json.loads(call_args[0][1])
        assert payload["price_usd_per_lb"] == pytest.approx(2.45)
        assert call_args[1]["ex"] == CACHE_TTL_SECONDS

        # Should publish to the channel
        redis_mock.publish.assert_called_once()
        channel, msg = redis_mock.publish.call_args[0]
        assert channel == REDIS_CHANNEL
        published = json.loads(msg)
        assert published["price_usd_per_lb"] == pytest.approx(2.45)

    def test_handles_redis_error_gracefully(self):
        redis_mock = MagicMock()
        redis_mock.set.side_effect = Exception("Connection refused")
        quote = _make_quote()

        # Should not raise
        publish_price(redis_mock, quote)


class TestGetCachedPrice:
    def test_returns_dict_when_cache_hit(self):
        payload = json.dumps({
            "price_usd_per_lb": 2.35,
            "observed_at": "2025-06-01T12:00:00+00:00",
            "source_name": "Twelve Data (ICE KC1!)",
            "metadata": {},
        })
        redis_mock = MagicMock()
        redis_mock.get.return_value = payload.encode("utf-8")

        result = get_cached_price(redis_mock)

        assert result is not None
        assert result["price_usd_per_lb"] == pytest.approx(2.35)

    def test_returns_none_on_cache_miss(self):
        redis_mock = MagicMock()
        redis_mock.get.return_value = None

        result = get_cached_price(redis_mock)

        assert result is None

    def test_returns_none_on_redis_error(self):
        redis_mock = MagicMock()
        redis_mock.get.side_effect = Exception("timeout")

        result = get_cached_price(redis_mock)

        assert result is None
