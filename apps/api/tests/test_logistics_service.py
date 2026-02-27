"""Tests for logistics service."""

import pytest
from app.services.logistics import calc_landed_cost, _latest_usd_eur, DEFAULT_USD_EUR
from app.models.market import MarketObservation
from datetime import datetime, timezone


def test_calc_landed_cost_basic(db):
    """Test basic landed cost calculation."""
    result = calc_landed_cost(
        db,
        weight_kg=1000.0,
        green_price_usd_per_kg=5.0,
        freight_usd=500.0,
        handling_eur=100.0,
        inland_trucking_eur=150.0,
    )

    assert result["status"] == "ok"
    assert "breakdown_eur" in result
    assert result["breakdown_eur"]["total"] > 0
    assert result["breakdown_eur"]["landed_eur_per_kg"] > 0


def test_calc_landed_cost_with_duty(db):
    """Test landed cost calculation with customs duty."""
    result = calc_landed_cost(
        db,
        weight_kg=1000.0,
        green_price_usd_per_kg=5.0,
        duty_pct=0.10,  # 10% duty
        freight_usd=500.0,
    )

    assert result["breakdown_eur"]["duty"] > 0


def test_calc_landed_cost_with_vat(db):
    """Test landed cost calculation with VAT."""
    result = calc_landed_cost(
        db,
        weight_kg=1000.0,
        green_price_usd_per_kg=5.0,
        vat_pct=0.19,  # 19% German VAT
        freight_usd=500.0,
    )

    assert result["breakdown_eur"]["vat"] > 0


def test_calc_landed_cost_zero_weight(db):
    """Test landed cost calculation with zero weight."""
    with pytest.raises(ValueError, match="weight_kg must be > 0"):
        calc_landed_cost(db, weight_kg=0.0, green_price_usd_per_kg=5.0)


def test_calc_landed_cost_negative_price(db):
    """Test landed cost calculation with negative price."""
    with pytest.raises(ValueError, match="green_price_usd_per_kg must be >= 0"):
        calc_landed_cost(db, weight_kg=1000.0, green_price_usd_per_kg=-5.0)


def test_calc_landed_cost_uses_fx_from_db(db):
    """Test landed cost calculation uses FX rate from database."""
    # Add FX observation
    obs = MarketObservation(
        key="FX:USD_EUR", value=0.95, observed_at=datetime.now(timezone.utc)
    )
    db.add(obs)
    db.commit()

    result = calc_landed_cost(db, weight_kg=1000.0, green_price_usd_per_kg=5.0)

    assert result["fx"]["usd_eur"] == 0.95


def test_calc_landed_cost_fallback_fx(db):
    """Test landed cost calculation uses fallback FX when no data in DB."""
    result = calc_landed_cost(db, weight_kg=1000.0, green_price_usd_per_kg=5.0)

    assert result["fx"]["usd_eur"] == DEFAULT_USD_EUR
    assert result["fx"]["source"] == "fallback"


def test_calc_landed_cost_insurance_calculation(db):
    """Test insurance calculation in landed cost."""
    result = calc_landed_cost(
        db,
        weight_kg=1000.0,
        green_price_usd_per_kg=5.0,
        freight_usd=500.0,
        insurance_pct=0.01,  # 1% insurance
    )

    # Insurance should be calculated on goods + freight
    goods_eur = result["breakdown_eur"]["goods"]
    freight_eur = result["breakdown_eur"]["freight"]
    expected_insurance = (goods_eur + freight_eur) * 0.01

    assert abs(result["breakdown_eur"]["insurance"] - expected_insurance) < 0.01


def test_latest_usd_eur_with_data(db):
    """Test _latest_usd_eur returns most recent observation."""
    # Add old observation
    old_obs = MarketObservation(
        key="FX:USD_EUR",
        value=0.90,
        observed_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    db.add(old_obs)

    # Add new observation
    new_obs = MarketObservation(
        key="FX:USD_EUR", value=0.95, observed_at=datetime.now(timezone.utc)
    )
    db.add(new_obs)
    db.commit()

    rate, source = _latest_usd_eur(db)

    assert rate == 0.95
    assert "obs:" in source


def test_latest_usd_eur_without_data(db):
    """Test _latest_usd_eur returns fallback when no data."""
    rate, source = _latest_usd_eur(db)

    assert rate == DEFAULT_USD_EUR
    assert source == "fallback"
