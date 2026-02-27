"""Tests for scoring service."""

from app.services.scoring import (
    compute_cooperative_score,
    _clamp,
    _map_sca_to_score,
    _get_latest_observation,
    DEFAULT_WEIGHTS,
    ScoreBreakdown,
)
from app.models.cooperative import Cooperative
from app.models.market import MarketObservation
from datetime import datetime, timezone


def test_clamp_within_range():
    """Test _clamp keeps values within range."""
    assert _clamp(50.0) == 50.0
    assert _clamp(150.0) == 100.0
    assert _clamp(-10.0) == 0.0


def test_map_sca_to_score():
    """Test _map_sca_to_score converts SCA scores."""
    assert _map_sca_to_score(80.0) == 60.0
    assert _map_sca_to_score(90.0) == 100.0
    assert _map_sca_to_score(85.0) == 80.0


def test_get_latest_observation(db):
    """Test _get_latest_observation retrieves most recent."""
    obs1 = MarketObservation(
        key="TEST_KEY", value=1.0, observed_at=datetime(2024, 1, 1, tzinfo=timezone.utc)
    )
    obs2 = MarketObservation(
        key="TEST_KEY", value=2.0, observed_at=datetime.now(timezone.utc)
    )
    db.add_all([obs1, obs2])
    db.commit()

    result = _get_latest_observation(db, "TEST_KEY")

    assert result is not None
    assert result.value == 2.0


def test_get_latest_observation_not_found(db):
    """Test _get_latest_observation with no data."""
    result = _get_latest_observation(db, "NONEXISTENT")

    assert result is None


def test_compute_cooperative_score_with_quality_score(db):
    """Test computing score with quality score set."""
    coop = Cooperative(
        name="Test Coop",
        region="Cajamarca",
        quality_score=85.0,
        reliability_score=80.0,
        economics_score=75.0,
    )
    db.add(coop)
    db.commit()

    result = compute_cooperative_score(db, coop)

    assert isinstance(result, ScoreBreakdown)
    assert result.quality == 85.0
    assert result.reliability == 80.0
    assert result.economics == 75.0
    assert result.total is not None


def test_compute_cooperative_score_with_sca_score(db):
    """Test computing score with SCA score in meta."""
    coop = Cooperative(name="Test Coop", region="Cajamarca", meta={"sca_score": 85.0})
    db.add(coop)
    db.commit()

    result = compute_cooperative_score(db, coop)

    assert isinstance(result, ScoreBreakdown)
    assert result.quality is not None


def test_compute_cooperative_score_empty_coop(db):
    """Test computing score with minimal data."""
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()

    result = compute_cooperative_score(db, coop)

    assert isinstance(result, ScoreBreakdown)
    assert result.confidence >= 0.0
    assert result.confidence <= 1.0


def test_compute_cooperative_score_with_meta_reliability(db):
    """Test computing score with reliability in meta."""
    coop = Cooperative(name="Test Coop", region="Cajamarca", meta={"reliability": 90.0})
    db.add(coop)
    db.commit()

    result = compute_cooperative_score(db, coop)

    assert result.reliability == 90.0


def test_compute_cooperative_score_confidence(db):
    """Test confidence calculation."""
    # Cooperative with all scores
    coop_full = Cooperative(
        name="Full Coop",
        region="Cajamarca",
        quality_score=85.0,
        reliability_score=80.0,
        economics_score=75.0,
    )
    db.add(coop_full)

    # Cooperative with no scores
    coop_empty = Cooperative(name="Empty Coop", region="Junin")
    db.add(coop_empty)
    db.commit()

    result_full = compute_cooperative_score(db, coop_full)
    result_empty = compute_cooperative_score(db, coop_empty)

    # Full coop should have higher confidence
    assert result_full.confidence > result_empty.confidence


def test_default_weights():
    """Test default weights sum to 1.0."""
    total = sum(DEFAULT_WEIGHTS.values())
    assert abs(total - 1.0) < 0.01


def test_score_breakdown_dataclass():
    """Test ScoreBreakdown dataclass."""
    breakdown = ScoreBreakdown(
        quality=85.0,
        reliability=80.0,
        economics=75.0,
        total=80.0,
        confidence=0.9,
        reasons=["test reason"],
    )

    assert breakdown.quality == 85.0
    assert breakdown.total == 80.0
    assert breakdown.confidence == 0.9
