"""Tests for the ICE realtime price provider (Twelve Data integration)."""

from unittest.mock import MagicMock, patch

import pytest

from app.providers.ice_realtime import (
    fetch_twelve_data_coffee,
    fetch_realtime_coffee_price,
)
from app.providers.coffee_prices import CoffeeQuote


def _mock_httpx_response(json_data: dict, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    if status_code >= 400:
        mock.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    else:
        mock.raise_for_status.return_value = None
    return mock


class TestFetchTwelveDataCoffee:
    def test_returns_quote_on_success(self):
        resp = _mock_httpx_response({"price": "2.3500"})
        with patch("app.providers.ice_realtime.httpx.get", return_value=resp):
            quote = fetch_twelve_data_coffee("fake-api-key")

        assert quote is not None
        assert isinstance(quote, CoffeeQuote)
        assert quote.price_usd_per_lb == pytest.approx(2.35)
        assert quote.source_name == "Twelve Data (ICE KC1!)"
        assert quote.metadata["provider"] == "twelve_data"
        assert quote.metadata["exchange"] == "ICE"

    def test_returns_none_when_price_missing(self):
        resp = _mock_httpx_response({"code": 400, "message": "Invalid symbol"})
        with patch("app.providers.ice_realtime.httpx.get", return_value=resp):
            quote = fetch_twelve_data_coffee("fake-api-key")

        assert quote is None

    def test_returns_none_on_network_error(self):
        with patch("app.providers.ice_realtime.httpx.get", side_effect=Exception("timeout")):
            quote = fetch_twelve_data_coffee("fake-api-key")

        assert quote is None

    def test_returns_none_on_http_error(self):
        resp = _mock_httpx_response({}, status_code=429)
        with patch("app.providers.ice_realtime.httpx.get", return_value=resp):
            quote = fetch_twelve_data_coffee("fake-api-key")

        assert quote is None


class TestFetchRealtimeCoffeePrice:
    def test_uses_twelve_data_when_api_key_provided(self):
        mock_quote = CoffeeQuote(
            price_usd_per_lb=2.40,
            observed_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            source_name="Twelve Data (ICE KC1!)",
            source_url="https://api.twelvedata.com/price",
            raw_data="{}",
            metadata={"provider": "twelve_data"},
        )
        with patch(
            "app.providers.ice_realtime.fetch_twelve_data_coffee",
            return_value=mock_quote,
        ):
            result = fetch_realtime_coffee_price(api_key="fake-key")

        assert result is not None
        assert result.price_usd_per_lb == 2.40

    def test_falls_back_to_yahoo_when_twelve_data_fails(self):
        fallback_quote = CoffeeQuote(
            price_usd_per_lb=2.35,
            observed_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            source_name="Yahoo Finance",
            source_url="https://query1.finance.yahoo.com/",
            raw_data="{}",
            metadata={},
        )
        with patch(
            "app.providers.ice_realtime.fetch_twelve_data_coffee",
            return_value=None,
        ), patch(
            "app.providers.coffee_prices.fetch_yahoo_finance_coffee",
            return_value=fallback_quote,
        ):
            result = fetch_realtime_coffee_price(api_key="fake-key")

        assert result is not None
        assert result.source_name == "Yahoo Finance"

    def test_skips_twelve_data_when_no_api_key(self):
        fallback_quote = CoffeeQuote(
            price_usd_per_lb=2.30,
            observed_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            source_name="Yahoo Finance",
            source_url="https://query1.finance.yahoo.com/",
            raw_data="{}",
            metadata={},
        )
        with patch(
            "app.providers.ice_realtime.fetch_twelve_data_coffee"
        ) as mock_td, patch(
            "app.providers.coffee_prices.fetch_yahoo_finance_coffee",
            return_value=fallback_quote,
        ):
            result = fetch_realtime_coffee_price(api_key=None)

        # Twelve Data should NOT be called when no key is given
        mock_td.assert_not_called()
        assert result is not None
        assert result.source_name == "Yahoo Finance"

    def test_returns_none_when_all_sources_fail(self):
        with patch(
            "app.providers.ice_realtime.fetch_twelve_data_coffee",
            return_value=None,
        ), patch(
            "app.providers.coffee_prices.fetch_yahoo_finance_coffee",
            return_value=None,
        ):
            result = fetch_realtime_coffee_price(api_key="fake-key")

        assert result is None
