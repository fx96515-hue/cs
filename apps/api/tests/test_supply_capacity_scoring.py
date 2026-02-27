"""
Tests for supply capacity scoring algorithm.

Tests various scenarios for cooperative supply capacity evaluation.
"""

from app.models.cooperative import Cooperative
from app.services.cooperative_sourcing_analyzer import CooperativeSourcingAnalyzer


def test_high_volume_supply_capacity(db):
    """Test supply capacity scoring for high-volume cooperative."""
    coop = Cooperative(
        name="High Volume Coop",
        region="Cajamarca",
        operational_data={
            "annual_volume_kg": 150000,  # 150 tons - should score 30
            "farmer_count": 600,  # should score 20
            "storage_capacity_kg": 250000,  # should score 20
            "processing_facilities": ["wet_mill", "dry_mill"],  # should score 15
            "years_exporting": 12,  # should score 15
        },
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    analyzer = CooperativeSourcingAnalyzer(db)
    result = analyzer.check_supply_capacity(coop)

    assert result["score"] == 100, "High volume coop should score perfect 100"
    assert result["assessment"] == "strong"
    assert result["breakdown"]["volume"]["score"] == 30
    assert result["breakdown"]["farmers"]["score"] == 20
    assert result["breakdown"]["storage"]["score"] == 20
    assert result["breakdown"]["facilities"]["score"] == 15
    assert result["breakdown"]["experience"]["score"] == 15


def test_low_volume_supply_capacity(db):
    """Test supply capacity scoring for low-volume cooperative."""
    coop = Cooperative(
        name="Low Volume Coop",
        region="Puno",
        operational_data={
            "annual_volume_kg": 5000,  # 5 tons - should score 5
            "farmer_count": 30,  # should score 5
            "storage_capacity_kg": 10000,  # should score 5
            "processing_facilities": [],  # should score 0
            "years_exporting": 0,  # should score 2
        },
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    analyzer = CooperativeSourcingAnalyzer(db)
    result = analyzer.check_supply_capacity(coop)

    assert result["score"] == 17, "Low volume coop should score 17"
    assert result["assessment"] == "limited"
    assert result["breakdown"]["volume"]["score"] == 5
    assert result["breakdown"]["farmers"]["score"] == 5
    assert result["breakdown"]["storage"]["score"] == 5
    assert result["breakdown"]["facilities"]["score"] == 0
    assert result["breakdown"]["experience"]["score"] == 2


def test_medium_volume_supply_capacity(db):
    """Test supply capacity scoring for medium-volume cooperative."""
    coop = Cooperative(
        name="Medium Volume Coop",
        region="Junín",
        operational_data={
            "annual_volume_kg": 60000,  # 60 tons - should score 25
            "farmer_count": 250,  # should score 17
            "storage_capacity_kg": 120000,  # should score 17
            "processing_facilities": ["wet_mill"],  # should score 8
            "years_exporting": 6,  # should score 12
        },
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    analyzer = CooperativeSourcingAnalyzer(db)
    result = analyzer.check_supply_capacity(coop)

    assert result["score"] == 79, "Medium volume coop should score 79"
    assert result["assessment"] == "strong"
    assert result["breakdown"]["volume"]["score"] == 25
    assert result["breakdown"]["farmers"]["score"] == 17
    assert result["breakdown"]["storage"]["score"] == 17
    assert result["breakdown"]["facilities"]["score"] == 8
    assert result["breakdown"]["experience"]["score"] == 12


def test_empty_operational_data(db):
    """Test supply capacity scoring with no operational data."""
    coop = Cooperative(name="No Data Coop", region="Cusco", operational_data=None)
    db.add(coop)
    db.commit()
    db.refresh(coop)

    analyzer = CooperativeSourcingAnalyzer(db)
    result = analyzer.check_supply_capacity(coop)

    # Should get minimum scores: 5+5+5+0+2 = 17
    assert result["score"] == 17, "Coop with no data should score minimum 17"
    assert result["assessment"] == "limited"
