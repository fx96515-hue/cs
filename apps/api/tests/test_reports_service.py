"""Tests for reports service."""

from app.services.reports import generate_daily_report, _latest_by_key, _fmt_obs
from app.models.market import MarketObservation
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster
from datetime import datetime, timezone


def test_generate_daily_report_empty(db):
    """Test daily report generation with empty database."""
    markdown, payload = generate_daily_report(db)

    assert markdown is not None
    assert isinstance(markdown, str)
    assert payload is not None
    assert isinstance(payload, dict)


def test_generate_daily_report_with_market_data(db):
    """Test daily report with market observations."""
    # Add market observations
    obs1 = MarketObservation(
        key="FX:USD_EUR", value=0.92, unit="EUR", observed_at=datetime.now(timezone.utc)
    )
    obs2 = MarketObservation(
        key="COFFEE_C:USD_LB",
        value=2.50,
        unit="USD/LB",
        observed_at=datetime.now(timezone.utc),
    )
    db.add(obs1)
    db.add(obs2)
    db.commit()

    markdown, payload = generate_daily_report(db)

    # Check that data is present (case insensitive)
    assert "usd" in markdown.lower() or "eur" in markdown.lower()


def test_generate_daily_report_with_cooperatives(db):
    """Test daily report with cooperatives."""
    coop1 = Cooperative(name="Test Coop 1", total_score=85.0, confidence=0.9)
    coop2 = Cooperative(name="Test Coop 2", total_score=75.0, confidence=0.8)
    db.add(coop1)
    db.add(coop2)
    db.commit()

    markdown, payload = generate_daily_report(db)

    assert "cooperative" in markdown.lower() or "coop" in markdown.lower()


def test_generate_daily_report_with_roasters(db):
    """Test daily report with roasters."""
    roaster1 = Roaster(name="Test Roaster 1", peru_focus=True)
    roaster2 = Roaster(name="Test Roaster 2", peru_focus=False)
    db.add(roaster1)
    db.add(roaster2)
    db.commit()

    markdown, payload = generate_daily_report(db)

    assert markdown is not None


def test_latest_by_key_with_data(db):
    """Test _latest_by_key retrieves most recent observations."""
    # Add observations
    old_obs = MarketObservation(
        key="FX:USD_EUR",
        value=0.90,
        observed_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    new_obs = MarketObservation(
        key="FX:USD_EUR", value=0.92, observed_at=datetime.now(timezone.utc)
    )
    db.add(old_obs)
    db.add(new_obs)
    db.commit()

    result = _latest_by_key(db, ["FX:USD_EUR"])

    assert result["FX:USD_EUR"] is not None
    assert result["FX:USD_EUR"].value == 0.92


def test_latest_by_key_missing_data(db):
    """Test _latest_by_key with missing keys."""
    result = _latest_by_key(db, ["NONEXISTENT_KEY"])

    assert result["NONEXISTENT_KEY"] is None


def test_fmt_obs_with_observation(db):
    """Test _fmt_obs formats observation correctly."""
    obs = MarketObservation(
        key="FX:USD_EUR",
        value=0.92,
        unit="EUR",
        currency="USD",
        observed_at=datetime.now(timezone.utc),
    )

    result = _fmt_obs(obs)

    assert "0.92" in result
    assert "EUR" in result


def test_fmt_obs_without_observation():
    """Test _fmt_obs handles None observation."""
    result = _fmt_obs(None)

    assert result == "-"
