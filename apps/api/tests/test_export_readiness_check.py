"""
Tests for export readiness checking algorithm.

Tests various scenarios for cooperative export readiness evaluation.
"""

from app.models.cooperative import Cooperative
from app.services.cooperative_sourcing_analyzer import CooperativeSourcingAnalyzer


def test_full_export_readiness(db):
    """Test export readiness with all requirements met."""
    coop = Cooperative(
        name="Export Ready Coop",
        region="Cajamarca",
        export_readiness={
            "has_export_license": True,
            "license_expiry_date": "2026-12-31",
            "senasa_registered": True,
            "certifications": ["Organic", "Fair Trade", "Rainforest Alliance"],
            "customs_issues_count": 0,
            "has_document_coordinator": True,
        },
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    analyzer = CooperativeSourcingAnalyzer(db)
    result = analyzer.check_export_readiness(coop)

    assert result["score"] == 100, "Fully ready coop should score perfect 100"
    assert result["assessment"] == "ready"
    assert result["breakdown"]["license"]["score"] == 25
    assert result["breakdown"]["senasa"]["score"] == 25
    assert result["breakdown"]["certifications"]["score"] == 25
    assert result["breakdown"]["customs"]["score"] == 15
    assert result["breakdown"]["coordinator"]["score"] == 10


def test_minimal_export_readiness(db):
    """Test export readiness with minimal requirements."""
    coop = Cooperative(
        name="Minimal Ready Coop",
        region="San Martín",
        export_readiness={
            "has_export_license": False,
            "license_expiry_date": None,
            "senasa_registered": False,
            "certifications": [],
            "customs_issues_count": 10,
            "has_document_coordinator": False,
        },
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    analyzer = CooperativeSourcingAnalyzer(db)
    result = analyzer.check_export_readiness(coop)

    assert result["score"] == 5, "Minimally ready coop should score 5"
    assert result["assessment"] == "not_ready"
    assert result["breakdown"]["license"]["score"] == 0
    assert result["breakdown"]["senasa"]["score"] == 0
    assert result["breakdown"]["certifications"]["score"] == 5
    assert result["breakdown"]["customs"]["score"] == 0
    assert result["breakdown"]["coordinator"]["score"] == 0


def test_partial_export_readiness(db):
    """Test export readiness with some requirements met."""
    coop = Cooperative(
        name="Partial Ready Coop",
        region="Junín",
        export_readiness={
            "has_export_license": True,
            "license_expiry_date": None,  # Has license but no expiry
            "senasa_registered": True,
            "certifications": ["Organic", "Fair Trade"],  # 2 certs
            "customs_issues_count": 2,  # Some issues
            "has_document_coordinator": True,
        },
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    analyzer = CooperativeSourcingAnalyzer(db)
    result = analyzer.check_export_readiness(coop)

    # License (20) + SENASA (25) + Certs (20) + Customs (10) + Coordinator (10) = 85
    assert result["score"] == 85, "Partially ready coop should score 85"
    assert result["assessment"] == "ready"
    assert result["breakdown"]["license"]["score"] == 20
    assert result["breakdown"]["senasa"]["score"] == 25
    assert result["breakdown"]["certifications"]["score"] == 20
    assert result["breakdown"]["customs"]["score"] == 10
    assert result["breakdown"]["coordinator"]["score"] == 10


def test_empty_export_readiness(db):
    """Test export readiness with no data."""
    coop = Cooperative(name="No Data Coop", region="Cusco", export_readiness=None)
    db.add(coop)
    db.commit()
    db.refresh(coop)

    analyzer = CooperativeSourcingAnalyzer(db)
    result = analyzer.check_export_readiness(coop)

    # Should get minimum score: 0+0+5+15+0 = 20 (only certifications and customs get defaults)
    assert result["score"] == 20, "Coop with no data should score 20"
    assert result["assessment"] == "not_ready"
