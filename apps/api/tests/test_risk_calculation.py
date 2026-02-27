"""
Tests for risk calculation algorithm.

Tests various risk scenarios for cooperative sourcing evaluation.
"""

from app.models.cooperative import Cooperative
from app.services.cooperative_sourcing_analyzer import CooperativeSourcingAnalyzer


def test_low_risk_cooperative(db):
    """Test risk calculation for low-risk cooperative."""
    coop = Cooperative(
        name="Low Risk Coop",
        region="Junín",
        altitude_m=1400,
        quality_score=85,
        operational_data={"years_exporting": 8},
        export_readiness={"customs_issues_count": 0},
        financial_data={"annual_revenue_usd": 750000},
        communication_metrics={"avg_response_hours": 18, "missed_meetings": 0},
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    analyzer = CooperativeSourcingAnalyzer(db)
    result = analyzer.calculate_sourcing_risk(coop)

    # Financial: 5, Quality: 5, Delivery: 15, Geographic: 5, Communication: 0 = 30
    assert result["total_risk_score"] <= 30, "Low risk coop should have risk ≤30"
    # Risk of exactly 30 is at the boundary - could be "low" or "moderate"
    assert result["assessment"] in [
        "low",
        "moderate",
    ], f"Risk {result['total_risk_score']} should be low or moderate"


def test_high_risk_cooperative(db):
    """Test risk calculation for high-risk cooperative."""
    coop = Cooperative(
        name="High Risk Coop",
        region="Puno",
        altitude_m=2200,  # High altitude = higher geo risk
        quality_score=55,  # Low quality = high quality risk
        operational_data={
            "years_exporting": 1  # Low experience
        },
        export_readiness={
            "customs_issues_count": 8  # Many issues
        },
        financial_data={
            "annual_revenue_usd": 30000  # Very low revenue
        },
        communication_metrics={
            "avg_response_hours": 120,  # Very slow
            "missed_meetings": 5,  # Many missed
        },
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    analyzer = CooperativeSourcingAnalyzer(db)
    result = analyzer.calculate_sourcing_risk(coop)

    # Should have high risk score
    assert result["total_risk_score"] >= 60, "High risk coop should have risk ≥60"
    assert result["assessment"] == "high"


def test_moderate_risk_cooperative(db):
    """Test risk calculation for moderate-risk cooperative."""
    coop = Cooperative(
        name="Moderate Risk Coop",
        region="Cajamarca",
        altitude_m=1400,  # Lower altitude → 5 risk
        quality_score=75,  # Better quality → 10 risk
        operational_data={
            "years_exporting": 5  # More experience → 15 risk
        },
        export_readiness={
            "customs_issues_count": 1  # Fewer issues
        },
        financial_data={
            "annual_revenue_usd": 300000  # Better revenue → 10 risk
        },
        communication_metrics={
            "avg_response_hours": 40,  # Better response → 0 risk
            "missed_meetings": 1,  # Fewer missed → 1 risk
        },
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    analyzer = CooperativeSourcingAnalyzer(db)
    result = analyzer.calculate_sourcing_risk(coop)

    # Financial: 10, Quality: 10, Delivery: 17, Geographic: 5, Communication: 1 = 43
    assert 30 <= result["total_risk_score"] < 50, (
        f"Moderate risk coop should have risk between 30-50, got {result['total_risk_score']}"
    )
    assert result["assessment"] == "moderate"
