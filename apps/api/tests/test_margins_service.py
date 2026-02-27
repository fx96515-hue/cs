"""Tests for margins calculation service."""

import pytest
from pydantic_core import ValidationError
from app.services.margins import calc_margin
from app.schemas.margin import MarginCalcRequest


def test_basic_margin_calculation():
    """Test basic margin calculation with simple values."""
    req = MarginCalcRequest(
        purchase_price_per_kg=10.0,
        landed_costs_per_kg=2.0,
        yield_factor=0.84,
        roast_and_pack_costs_per_kg=3.0,
        selling_price_per_kg=20.0,
        purchase_currency="USD",
        selling_currency="EUR",
    )

    inputs, outputs = calc_margin(req)

    assert outputs["green_total_cost_per_kg"] == 12.0
    assert abs(outputs["cost_per_kg_roasted_from_green"] - 14.286) < 0.01
    assert abs(outputs["total_cost_per_kg_roasted"] - 17.286) < 0.01
    assert abs(outputs["gross_margin_per_kg"] - 2.714) < 0.01
    assert abs(outputs["gross_margin_pct"] - 13.57) < 0.1


def test_margin_calculation_with_fx():
    """Test margin calculation with FX conversion."""
    req = MarginCalcRequest(
        purchase_price_per_kg=10.0,
        landed_costs_per_kg=2.0,
        yield_factor=0.84,
        roast_and_pack_costs_per_kg=3.0,
        selling_price_per_kg=20.0,
        purchase_currency="USD",
        selling_currency="EUR",
        fx_usd_to_eur=0.92,
    )

    inputs, outputs = calc_margin(req)

    assert "green_total_cost_per_kg_eur" in outputs
    assert abs(outputs["green_total_cost_per_kg_eur"] - 11.04) < 0.01
    assert "total_cost_per_kg_roasted_eur" in outputs


def test_margin_calculation_zero_selling_price():
    """Test margin calculation with zero selling price."""
    req = MarginCalcRequest(
        purchase_price_per_kg=10.0,
        landed_costs_per_kg=2.0,
        yield_factor=0.84,
        roast_and_pack_costs_per_kg=3.0,
        selling_price_per_kg=0.0,
        purchase_currency="USD",
        selling_currency="EUR",
    )

    inputs, outputs = calc_margin(req)

    assert outputs["gross_margin_pct"] is None


def test_margin_calculation_invalid_yield_factor():
    """Test margin calculation with invalid yield factor."""
    with pytest.raises(ValidationError, match="Input should be greater than 0"):
        MarginCalcRequest(
            purchase_price_per_kg=10.0,
            landed_costs_per_kg=2.0,
            yield_factor=0.0,
            roast_and_pack_costs_per_kg=3.0,
            selling_price_per_kg=20.0,
            purchase_currency="USD",
            selling_currency="EUR",
        )


def test_margin_calculation_yield_factor_greater_than_one():
    """Test margin calculation with yield factor > 1."""
    with pytest.raises(
        ValidationError, match="Input should be less than or equal to 1"
    ):
        MarginCalcRequest(
            purchase_price_per_kg=10.0,
            landed_costs_per_kg=2.0,
            yield_factor=1.5,
            roast_and_pack_costs_per_kg=3.0,
            selling_price_per_kg=20.0,
            purchase_currency="USD",
            selling_currency="EUR",
        )


def test_margin_calculation_high_margin():
    """Test margin calculation with high margin scenario."""
    req = MarginCalcRequest(
        purchase_price_per_kg=5.0,
        landed_costs_per_kg=1.0,
        yield_factor=0.85,
        roast_and_pack_costs_per_kg=2.0,
        selling_price_per_kg=25.0,
        purchase_currency="USD",
        selling_currency="EUR",
    )

    inputs, outputs = calc_margin(req)

    assert outputs["gross_margin_pct"] > 50.0


def test_margin_calculation_negative_margin():
    """Test margin calculation with negative margin (loss)."""
    req = MarginCalcRequest(
        purchase_price_per_kg=15.0,
        landed_costs_per_kg=5.0,
        yield_factor=0.80,
        roast_and_pack_costs_per_kg=8.0,
        selling_price_per_kg=20.0,
        purchase_currency="USD",
        selling_currency="EUR",
    )

    inputs, outputs = calc_margin(req)

    assert outputs["gross_margin_per_kg"] < 0


def test_margin_calculation_perfect_yield():
    """Test margin calculation with perfect yield factor (1.0)."""
    req = MarginCalcRequest(
        purchase_price_per_kg=10.0,
        landed_costs_per_kg=2.0,
        yield_factor=1.0,
        roast_and_pack_costs_per_kg=3.0,
        selling_price_per_kg=20.0,
        purchase_currency="USD",
        selling_currency="EUR",
    )

    inputs, outputs = calc_margin(req)

    assert outputs["cost_per_kg_roasted_from_green"] == 12.0
    assert outputs["total_cost_per_kg_roasted"] == 15.0


def test_margin_calculation_includes_computed_timestamp():
    """Test that margin calculation includes timestamp."""
    req = MarginCalcRequest(
        purchase_price_per_kg=10.0,
        landed_costs_per_kg=2.0,
        yield_factor=0.84,
        roast_and_pack_costs_per_kg=3.0,
        selling_price_per_kg=20.0,
        purchase_currency="USD",
        selling_currency="EUR",
    )

    inputs, outputs = calc_margin(req)

    assert "computed_at" in outputs
    assert outputs["computed_at"] is not None


def test_margin_calculation_without_fx():
    """Test margin calculation without FX rate provided."""
    req = MarginCalcRequest(
        purchase_price_per_kg=10.0,
        landed_costs_per_kg=2.0,
        yield_factor=0.84,
        roast_and_pack_costs_per_kg=3.0,
        selling_price_per_kg=20.0,
        purchase_currency="USD",
        selling_currency="EUR",
    )

    inputs, outputs = calc_margin(req)

    assert "green_total_cost_per_kg_eur" not in outputs
    assert "total_cost_per_kg_roasted_eur" not in outputs
