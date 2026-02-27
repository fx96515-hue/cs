"""Tests for dedup merge functionality."""

import pytest
from app.services.dedup import merge_entities, get_merge_history
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster
from app.models.entity_alias import EntityAlias


def test_merge_cooperatives(db):
    """Test merging two cooperatives."""
    coop1 = Cooperative(
        name="Coffee Cooperative",
        region="Cajamarca",
        quality_score=80.0,
        website="https://example.com",
    )
    coop2 = Cooperative(
        name="Coffee Coop",
        region="Cajamarca",
        quality_score=85.0,
        contact_email="info@coop.com",
    )
    db.add_all([coop1, coop2])
    db.commit()
    db.refresh(coop1)
    db.refresh(coop2)

    # Merge coop2 into coop1
    result = merge_entities(
        db, entity_type="cooperative", keep_id=coop1.id, merge_id=coop2.id
    )

    assert result["status"] == "ok"
    assert result["keep_id"] == coop1.id
    assert result["merge_id"] == coop2.id
    assert "contact_email" in result["merged_fields"]  # coop1 didn't have email

    # Check that alias was created
    alias = db.query(EntityAlias).filter_by(entity_id=coop1.id).first()
    assert alias is not None
    assert alias.alias == "Coffee Coop"

    # Check that coop2 is archived
    db.refresh(coop2)
    assert coop2.status == "archived"


def test_merge_roasters(db):
    """Test merging two roasters."""
    roaster1 = Roaster(name="Berlin Roasters", city="Berlin", total_score=75.0)
    roaster2 = Roaster(
        name="Berlin Coffee",
        city="Berlin",
        total_score=80.0,
        website="https://berlin.com",
    )
    db.add_all([roaster1, roaster2])
    db.commit()
    db.refresh(roaster1)
    db.refresh(roaster2)

    result = merge_entities(
        db, entity_type="roaster", keep_id=roaster1.id, merge_id=roaster2.id
    )

    assert result["status"] == "ok"
    assert "website" in result["merged_fields"]
    assert "total_score" in result["merged_fields"]


def test_merge_invalid_entity_type(db):
    """Test merge with invalid entity type."""
    with pytest.raises(ValueError, match="entity_type must be"):
        merge_entities(db, entity_type="invalid", keep_id=1, merge_id=2)


def test_merge_same_entity(db):
    """Test merge fails when trying to merge entity with itself."""
    coop = Cooperative(name="Test Coop")
    db.add(coop)
    db.commit()
    db.refresh(coop)

    with pytest.raises(ValueError, match="Cannot merge entity with itself"):
        merge_entities(db, entity_type="cooperative", keep_id=coop.id, merge_id=coop.id)


def test_merge_nonexistent_entity(db):
    """Test merge fails with nonexistent entity."""
    with pytest.raises(ValueError, match="not found"):
        merge_entities(db, entity_type="cooperative", keep_id=999, merge_id=998)


def test_merge_history(db):
    """Test retrieving merge history."""
    coop1 = Cooperative(name="Coop A")
    coop2 = Cooperative(name="Coop B")
    db.add_all([coop1, coop2])
    db.commit()
    db.refresh(coop1)
    db.refresh(coop2)

    # Perform merge
    merge_entities(db, entity_type="cooperative", keep_id=coop1.id, merge_id=coop2.id)

    # Get history
    history = get_merge_history(db, entity_type="cooperative", limit=10)

    assert len(history) > 0
    assert any(h["entity_id"] == coop1.id for h in history)


def test_merge_preserves_higher_scores(db):
    """Test that merge keeps higher scores."""
    coop1 = Cooperative(name="Coop A", quality_score=70.0, reliability_score=60.0)
    coop2 = Cooperative(name="Coop B", quality_score=80.0, reliability_score=50.0)
    db.add_all([coop1, coop2])
    db.commit()
    db.refresh(coop1)
    db.refresh(coop2)

    merge_entities(db, entity_type="cooperative", keep_id=coop1.id, merge_id=coop2.id)

    db.refresh(coop1)
    # Should keep higher quality_score from coop2
    assert coop1.quality_score == 80.0
    # Should keep higher reliability_score from coop1
    assert coop1.reliability_score == 60.0
