"""Tests for auto-outreach service."""

import pytest
from app.services.auto_outreach import (
    select_top_candidates,
    get_outreach_suggestions,
    get_entity_outreach_status,
)
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster
from app.models.entity_event import EntityEvent


def test_select_top_candidates_cooperatives(db):
    """Test selecting top cooperative candidates."""
    # Create cooperatives with different scores
    coop1 = Cooperative(
        name="High Score Coop",
        region="Cajamarca",
        quality_score=90.0,
        reliability_score=85.0,
        economics_score=88.0,
        total_score=87.7,
        status="active",
    )
    coop2 = Cooperative(
        name="Medium Score Coop",
        region="Junin",
        quality_score=75.0,
        reliability_score=70.0,
        economics_score=72.0,
        total_score=72.3,
        status="active",
    )
    coop3 = Cooperative(
        name="Low Score Coop",
        region="Cusco",
        quality_score=50.0,
        reliability_score=55.0,
        economics_score=52.0,
        total_score=52.3,
        status="active",
    )
    db.add_all([coop1, coop2, coop3])
    db.commit()

    # Select top candidates with minimum scores
    candidates = select_top_candidates(
        db, entity_type="cooperative", min_quality_score=70.0, limit=10
    )

    # Should only return coop1 and coop2
    assert len(candidates) == 2
    assert (
        candidates[0]["total_score"] >= candidates[1]["total_score"]
    )  # Sorted by score


def test_select_top_candidates_with_region_filter(db):
    """Test selecting candidates with region filter."""
    coop1 = Cooperative(
        name="Cajamarca Coop",
        region="Cajamarca",
        quality_score=85.0,
        status="active",
    )
    coop2 = Cooperative(
        name="Junin Coop",
        region="Junin",
        quality_score=90.0,
        status="active",
    )
    db.add_all([coop1, coop2])
    db.commit()

    candidates = select_top_candidates(
        db, entity_type="cooperative", region="Cajamarca", limit=10
    )

    assert len(candidates) == 1
    assert candidates[0]["region"] == "Cajamarca"


def test_select_top_candidates_with_certification_filter(db):
    """Test selecting candidates with certification filter."""
    coop1 = Cooperative(
        name="Organic Coop",
        certifications="Organic, Fair Trade",
        quality_score=85.0,
        status="active",
    )
    coop2 = Cooperative(
        name="Regular Coop",
        certifications="",
        quality_score=90.0,
        status="active",
    )
    db.add_all([coop1, coop2])
    db.commit()

    candidates = select_top_candidates(
        db, entity_type="cooperative", certification="Organic", limit=10
    )

    assert len(candidates) == 1
    assert "Organic" in candidates[0]["certifications"]


def test_select_top_candidates_roasters(db):
    """Test selecting top roaster candidates."""
    roaster1 = Roaster(
        name="High Quality Roaster",
        city="Berlin",
        total_score=86.7,
        status="active",
    )
    roaster2 = Roaster(
        name="Medium Roaster",
        city="Munich",
        total_score=73.7,
        status="active",
    )
    db.add_all([roaster1, roaster2])
    db.commit()

    candidates = select_top_candidates(db, entity_type="roaster", limit=10)

    assert len(candidates) >= 1
    assert candidates[0]["name"] == "High Quality Roaster"


def test_select_top_candidates_excludes_inactive(db):
    """Test that inactive entities are excluded."""
    coop1 = Cooperative(
        name="Active Coop",
        quality_score=85.0,
        status="active",
    )
    coop2 = Cooperative(
        name="Archived Coop",
        quality_score=90.0,
        status="archived",
    )
    db.add_all([coop1, coop2])
    db.commit()

    candidates = select_top_candidates(db, entity_type="cooperative", limit=10)

    assert len(candidates) == 1
    assert candidates[0]["name"] == "Active Coop"


def test_select_top_candidates_invalid_entity_type(db):
    """Test error handling for invalid entity type."""
    with pytest.raises(ValueError, match="entity_type must be"):
        select_top_candidates(db, entity_type="invalid", limit=10)


def test_get_outreach_suggestions(db):
    """Test getting AI-suggested outreach targets."""
    coop1 = Cooperative(
        name="High Score Coop",
        quality_score=80.0,
        reliability_score=75.0,
        status="active",
    )
    coop2 = Cooperative(
        name="Low Score Coop",
        quality_score=50.0,
        reliability_score=45.0,
        status="active",
    )
    db.add_all([coop1, coop2])
    db.commit()

    suggestions = get_outreach_suggestions(db, entity_type="cooperative", limit=10)

    # Should only suggest high-scoring entities
    assert len(suggestions) >= 1
    assert all(s["quality_score"] >= 70.0 for s in suggestions)


def test_get_entity_outreach_status_not_contacted(db):
    """Test getting status for entity not yet contacted."""
    coop = Cooperative(name="Test Coop", status="active")
    db.add(coop)
    db.commit()

    status = get_entity_outreach_status(
        db, entity_type="cooperative", entity_id=coop.id
    )

    assert status["status"] == "not_contacted"
    assert len(status["events"]) == 0


def test_get_entity_outreach_status_with_history(db):
    """Test getting status for entity with outreach history."""
    coop = Cooperative(name="Test Coop", status="active")
    db.add(coop)
    db.commit()

    # Add outreach event
    event = EntityEvent(
        entity_type="cooperative",
        entity_id=coop.id,
        event_type="outreach_generated",
        payload={"language": "de", "purpose": "sourcing_pitch"},
    )
    db.add(event)
    db.commit()

    status = get_entity_outreach_status(
        db, entity_type="cooperative", entity_id=coop.id
    )

    assert status["status"] in ["pending", "follow_up_needed"]
    assert len(status["events"]) == 1
