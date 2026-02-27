"""Tests for coffee prices provider."""

from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.providers.coffee_prices import (
    fetch_yahoo_finance_coffee,
    fetch_stooq_coffee,
    fetch_ico_fallback,
    fetch_coffee_price,
    CoffeeQuote,
)


def test_coffee_quote_dataclass():
    """Test CoffeeQuote dataclass creation."""
    quote = CoffeeQuote(
        price_usd_per_lb=2.10,
        observed_at=datetime.now(timezone.utc),
        source_name="Test",
        source_url="https://test.com",
        raw_data="{}",
        metadata={"test": True},
    )

    assert quote.price_usd_per_lb == 2.10
    assert quote.source_name == "Test"
    assert quote.metadata["test"] is True


def test_fetch_ico_fallback():
    """Test ICO fallback always returns a valid quote."""
    quote = fetch_ico_fallback()

    assert quote is not None
    assert quote.price_usd_per_lb == 2.10
    assert quote.source_name == "ICO Static Fallback"
    assert quote.metadata["fallback"] is True


def test_fetch_yahoo_finance_coffee_success():
    """Test fetching coffee price from Yahoo Finance with mocked response."""
    mock_response_data = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "regularMarketPrice": 210.5,
                        "regularMarketTime": 1704067200,
                        "currency": "USD",
                        "exchangeName": "ICE",
                    }
                }
            ]
        }
    }

    with patch("app.providers.coffee_prices.httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        quote = fetch_yahoo_finance_coffee()

        assert quote is not None
        assert quote.price_usd_per_lb == 210.5
        assert quote.source_name == "Yahoo Finance"
        assert "KC=F" in quote.source_url


def test_fetch_yahoo_finance_coffee_network_error():
    """Test Yahoo Finance fetch with network error."""
    with patch("app.providers.coffee_prices.httpx.get") as mock_get:
        mock_get.side_effect = Exception("Network error")

        quote = fetch_yahoo_finance_coffee()

        assert quote is None


def test_fetch_yahoo_finance_coffee_no_data():
    """Test Yahoo Finance fetch with empty results."""
    with patch("app.providers.coffee_prices.httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"chart": {"result": []}}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        quote = fetch_yahoo_finance_coffee()

        assert quote is None


def test_fetch_stooq_coffee_with_mock():
    """Test fetching coffee price from Stooq."""
    with patch("app.providers.coffee_prices.fetch_stooq_last_close") as mock_stooq:
        from app.providers.stooq import OhlcQuote

        mock_stooq.return_value = OhlcQuote(
            symbol="KC.F",
            close=205.0,
            observed_at=datetime.now(timezone.utc),
            source_url="https://stooq.com/q/d/l/?s=kc.f&i=d",
            raw_text="Date,Close\n2024-01-01,205.0",
        )

        quote = fetch_stooq_coffee()

        assert quote is not None
        assert quote.price_usd_per_lb == 205.0
        assert quote.source_name == "Stooq"


def test_fetch_stooq_coffee_failure():
    """Test Stooq coffee fetch when provider fails."""
    with patch("app.providers.coffee_prices.fetch_stooq_last_close") as mock_stooq:
        mock_stooq.return_value = None

        quote = fetch_stooq_coffee()

        assert quote is None


def test_fetch_coffee_price_fallback_chain():
    """Test coffee price fetch tries all sources in order."""
    with patch("app.providers.coffee_prices.fetch_yahoo_finance_coffee") as mock_yahoo:
        with patch("app.providers.coffee_prices.fetch_stooq_coffee") as mock_stooq:
            # Yahoo fails, Stooq succeeds
            mock_yahoo.return_value = None
            mock_stooq.return_value = CoffeeQuote(
                price_usd_per_lb=205.0,
                observed_at=datetime.now(timezone.utc),
                source_name="Stooq",
                source_url="https://test.com",
                raw_data="{}",
                metadata={},
            )

            quote = fetch_coffee_price()

            assert quote is not None
            assert quote.source_name == "Stooq"
            mock_yahoo.assert_called_once()
            mock_stooq.assert_called_once()


def test_fetch_coffee_price_all_sources_fail_with_fallback():
    """Test coffee price fetch when all sources fail but fallback enabled."""
    with patch("app.providers.coffee_prices.fetch_yahoo_finance_coffee") as mock_yahoo:
        with patch("app.providers.coffee_prices.fetch_stooq_coffee") as mock_stooq:
            mock_yahoo.return_value = None
            mock_stooq.return_value = None

            quote = fetch_coffee_price(use_fallback=True)

            assert quote is not None
            assert quote.source_name == "ICO Static Fallback"
            assert quote.price_usd_per_lb == 2.10


def test_fetch_coffee_price_all_sources_fail_no_fallback():
    """Test coffee price fetch when all sources fail and no fallback."""
    with patch("app.providers.coffee_prices.fetch_yahoo_finance_coffee") as mock_yahoo:
        with patch("app.providers.coffee_prices.fetch_stooq_coffee") as mock_stooq:
            mock_yahoo.return_value = None
            mock_stooq.return_value = None

            quote = fetch_coffee_price(use_fallback=False)

            assert quote is None
