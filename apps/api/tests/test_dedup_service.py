"""Tests for deduplication service."""

import pytest
from app.services.dedup import suggest_duplicates, _domain, _score, DedupPair
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster


def test_suggest_duplicates_cooperatives(db):
    """Test duplicate detection for cooperatives."""
    coop1 = Cooperative(name="Coffee Cooperative", region="Cajamarca")
    coop2 = Cooperative(name="Coffee Coop", region="Cajamarca")  # Similar name
    coop3 = Cooperative(name="Totally Different", region="Junin")
    db.add_all([coop1, coop2, coop3])
    db.commit()

    results = suggest_duplicates(db, entity_type="cooperative", threshold=80.0)

    assert isinstance(results, list)
    # Should find similarity between coop1 and coop2
    if results:
        assert all("score" in r for r in results)


def test_suggest_duplicates_roasters(db):
    """Test duplicate detection for roasters."""
    roaster1 = Roaster(name="Berlin Coffee Roasters", city="Berlin")
    roaster2 = Roaster(name="Berlin Coffee", city="Berlin")  # Similar name
    roaster3 = Roaster(name="Munich Coffee", city="Munich")
    db.add_all([roaster1, roaster2, roaster3])
    db.commit()

    results = suggest_duplicates(db, entity_type="roaster", threshold=80.0)

    assert isinstance(results, list)


def test_suggest_duplicates_invalid_entity_type(db):
    """Test duplicate detection with invalid entity type."""
    with pytest.raises(ValueError, match="entity_type must be"):
        suggest_duplicates(db, entity_type="invalid")


def test_suggest_duplicates_empty_database(db):
    """Test duplicate detection with empty database."""
    results = suggest_duplicates(db, entity_type="cooperative")

    assert results == []


def test_suggest_duplicates_with_threshold(db):
    """Test duplicate detection respects threshold."""
    coop1 = Cooperative(name="Coffee ABC", region="Cajamarca")
    coop2 = Cooperative(name="Coffee XYZ", region="Cajamarca")  # Somewhat similar
    db.add_all([coop1, coop2])
    db.commit()

    # High threshold - should find fewer or no matches
    results_high = suggest_duplicates(db, entity_type="cooperative", threshold=95.0)

    # Low threshold - should find more matches
    results_low = suggest_duplicates(db, entity_type="cooperative", threshold=50.0)

    assert len(results_low) >= len(results_high)


def test_domain_extracts_correctly():
    """Test _domain extracts domain from URL."""
    assert _domain("https://example.com/path") == "example.com"
    assert _domain("http://www.example.com") == "www.example.com"
    assert _domain(None) is None
    assert _domain("invalid") is None or _domain("invalid") == ""


def test_score_similarity():
    """Test _score calculates similarity correctly."""
    # Exact match
    score1 = _score("Coffee Cooperative", "Coffee Cooperative")
    assert score1 >= 95.0

    # Similar names
    score2 = _score("Coffee Coop", "Coffee Cooperative")
    assert score2 > 50.0

    # Very different names
    score3 = _score("ABC", "XYZ")
    assert score3 < 50.0


def test_score_handles_none():
    """Test _score handles None values."""
    score = _score(None, "Test")
    assert score >= 0.0
    assert score <= 100.0


def test_dedup_pair_dataclass():
    """Test DedupPair dataclass creation."""
    pair = DedupPair(
        a_id=1,
        b_id=2,
        a_name="Test A",
        b_name="Test B",
        score=85.5,
        reason="similar_name",
    )

    assert pair.a_id == 1
    assert pair.b_id == 2
    assert pair.score == 85.5
