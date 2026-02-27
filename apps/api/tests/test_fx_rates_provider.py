"""Tests for FX rates provider."""

from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.providers.fx_rates import (
    fetch_exchangerate_api_fx,
    fetch_frankfurter_fx,
    fetch_ecb_fx_wrapped,
    fetch_fx_rate,
    FxRate,
)


def test_fx_rate_dataclass():
    """Test FxRate dataclass creation."""
    rate = FxRate(
        base="USD",
        quote="EUR",
        rate=0.92,
        observed_at=datetime.now(timezone.utc),
        source_name="Test",
        source_url="https://test.com",
        raw_data="{}",
        metadata={"test": True},
    )

    assert rate.base == "USD"
    assert rate.quote == "EUR"
    assert rate.rate == 0.92


def test_fetch_exchangerate_api_fx_success():
    """Test fetching FX rate from ExchangeRate-API."""
    mock_response_data = {
        "base_code": "USD",
        "rates": {"EUR": 0.92, "GBP": 0.79},
        "time_last_update_unix": 1704067200,
    }

    with patch("app.providers.fx_rates.httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        rate = fetch_exchangerate_api_fx("USD", "EUR")

        assert rate is not None
        assert rate.base == "USD"
        assert rate.quote == "EUR"
        assert rate.rate == 0.92
        assert rate.source_name == "ExchangeRate-API"


def test_fetch_exchangerate_api_fx_same_currency():
    """Test ExchangeRate-API with same currency."""
    rate = fetch_exchangerate_api_fx("USD", "USD")
    assert rate is None


def test_fetch_exchangerate_api_fx_network_error():
    """Test ExchangeRate-API with network error."""
    with patch("app.providers.fx_rates.httpx.get") as mock_get:
        mock_get.side_effect = Exception("Network error")

        rate = fetch_exchangerate_api_fx("USD", "EUR")

        assert rate is None


def test_fetch_frankfurter_fx_success():
    """Test fetching FX rate from Frankfurter API."""
    mock_response_data = {
        "amount": 1.0,
        "base": "USD",
        "date": "2024-01-01",
        "rates": {"EUR": 0.92},
    }

    with patch("app.providers.fx_rates.httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        rate = fetch_frankfurter_fx("USD", "EUR")

        assert rate is not None
        assert rate.base == "USD"
        assert rate.quote == "EUR"
        assert rate.rate == 0.92
        assert rate.source_name == "Frankfurter"


def test_fetch_frankfurter_fx_no_rate():
    """Test Frankfurter with missing rate."""
    mock_response_data = {
        "amount": 1.0,
        "base": "USD",
        "date": "2024-01-01",
        "rates": {},
    }

    with patch("app.providers.fx_rates.httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        rate = fetch_frankfurter_fx("USD", "EUR")

        assert rate is None


def test_fetch_ecb_fx_wrapped():
    """Test ECB FX wrapper."""
    with patch("app.providers.fx_rates.fetch_ecb_fx") as mock_ecb:
        from app.providers.ecb_fx import FxQuote

        mock_ecb.return_value = FxQuote(
            base="USD",
            quote="EUR",
            rate=0.92,
            observed_at=datetime.now(timezone.utc),
            source_url="https://ecb.europa.eu/test",
            raw_text="<xml></xml>",
        )

        rate = fetch_ecb_fx_wrapped("USD", "EUR")

        assert rate is not None
        assert rate.base == "USD"
        assert rate.source_name == "ECB"


def test_fetch_fx_rate_fallback_chain():
    """Test FX rate fetch tries all sources in order."""
    with patch("app.providers.fx_rates.fetch_ecb_fx_wrapped") as mock_ecb:
        with patch("app.providers.fx_rates.fetch_exchangerate_api_fx") as mock_exr:
            # ECB fails, ExchangeRate-API succeeds
            mock_ecb.return_value = None
            mock_exr.return_value = FxRate(
                base="USD",
                quote="EUR",
                rate=0.92,
                observed_at=datetime.now(timezone.utc),
                source_name="ExchangeRate-API",
                source_url="https://test.com",
                raw_data="{}",
                metadata={},
            )

            rate = fetch_fx_rate("USD", "EUR")

            assert rate is not None
            assert rate.source_name == "ExchangeRate-API"
            mock_ecb.assert_called_once()
            mock_exr.assert_called_once()


def test_fetch_fx_rate_all_sources_fail():
    """Test FX rate fetch when all sources fail."""
    with patch("app.providers.fx_rates.fetch_ecb_fx_wrapped") as mock_ecb:
        with patch("app.providers.fx_rates.fetch_exchangerate_api_fx") as mock_exr:
            with patch("app.providers.fx_rates.fetch_frankfurter_fx") as mock_frank:
                mock_ecb.return_value = None
                mock_exr.return_value = None
                mock_frank.return_value = None

                rate = fetch_fx_rate("USD", "EUR")

                assert rate is None


def test_fetch_fx_rate_case_insensitive():
    """Test that currency codes are case-insensitive."""
    with patch("app.providers.fx_rates.fetch_ecb_fx_wrapped") as mock_ecb:
        mock_ecb.return_value = FxRate(
            base="USD",
            quote="EUR",
            rate=0.92,
            observed_at=datetime.now(timezone.utc),
            source_name="ECB",
            source_url="https://test.com",
            raw_data="{}",
            metadata={},
        )

        rate = fetch_fx_rate("usd", "eur")

        assert rate is not None
        # Should normalize to uppercase
        mock_ecb.assert_called_with("USD", "EUR", 20.0)
