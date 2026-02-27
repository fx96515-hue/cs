"""
Tests for price benchmarking algorithm.

Tests various pricing scenarios and competitiveness calculations.
"""

from app.models.cooperative import Cooperative
from app.models.region import Region
from app.services.cooperative_sourcing_analyzer import CooperativeSourcingAnalyzer


def test_competitive_pricing(db):
    """Test competitive pricing scenario."""
    # Benchmark price from ICO fallback is 4.85
    coop = Cooperative(
        name="Competitive Price Coop",
        region="Cajamarca",
        financial_data={
            "fob_price_per_kg": 4.80  # Very close to benchmark
        },
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    analyzer = CooperativeSourcingAnalyzer(db)
    result = analyzer.benchmark_pricing(coop)

    # Price diff: (4.80 - 4.85) / 4.85 = -1.03%
    # Score: 100 - (1.03 * 2) = ~97.94
    assert result["competitiveness_score"] >= 95, "Competitive price should score ≥95"
    assert result["assessment"] == "competitive"
    assert result["coop_price"] == 4.80
    assert result["benchmark_price"] == 4.85


def test_expensive_pricing(db):
    """Test expensive pricing scenario."""
    coop = Cooperative(
        name="Expensive Price Coop",
        region="Cusco",
        financial_data={
            "fob_price_per_kg": 6.00  # 23.7% above benchmark
        },
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    analyzer = CooperativeSourcingAnalyzer(db)
    result = analyzer.benchmark_pricing(coop)

    # Price diff: (6.00 - 4.85) / 4.85 = 23.7%
    # Score: 100 - (23.7 * 2) = ~52.6
    assert result["competitiveness_score"] < 60, "Expensive price should score <60"
    assert result["assessment"] in ["market_rate", "expensive"]
    assert result["coop_price"] == 6.00


def test_no_pricing_data(db):
    """Test pricing when no data available."""
    coop = Cooperative(name="No Price Coop", region="San Martín", financial_data=None)
    db.add(coop)
    db.commit()
    db.refresh(coop)

    analyzer = CooperativeSourcingAnalyzer(db)
    result = analyzer.benchmark_pricing(coop)

    assert result["competitiveness_score"] == 50, "No price data should default to 50"
    assert result["coop_price"] is None
    assert "No pricing data" in result["note"]


def test_pricing_with_ico_fallback(db):
    """Test pricing using ICO fallback benchmark."""
    # Create region first
    region = Region(name="Amazonas", country="Peru", production_share_pct=8.0)
    db.add(region)
    db.commit()

    coop = Cooperative(
        name="ICO Benchmark Coop",
        region="Amazonas",
        financial_data={"fob_price_per_kg": 5.00},
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    analyzer = CooperativeSourcingAnalyzer(db)
    result = analyzer.benchmark_pricing(coop)

    # Should use ICO fallback (4.85)
    assert result["benchmark_source"] == "ICO fallback"
    assert result["benchmark_price"] == 4.85
    # Price diff: (5.00 - 4.85) / 4.85 = 3.09%
    # Score: 100 - (3.09 * 2) = ~93.8
    assert result["competitiveness_score"] >= 90
    assert result["assessment"] == "competitive"
