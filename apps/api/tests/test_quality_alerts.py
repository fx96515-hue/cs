"""Tests for quality alerts service."""

from app.services.quality_alerts import (
    detect_score_changes,
    detect_certification_changes,
    get_alerts,
    get_alert_summary,
    acknowledge_alert,
)
from app.models.quality_alert import QualityAlert
from app.models.cooperative import Cooperative


def test_detect_score_changes_drop(db):
    """Test detecting score drops."""
    coop = Cooperative(name="Test Coop")
    db.add(coop)
    db.commit()

    old_scores = {
        "quality_score": 85.0,
        "reliability_score": 80.0,
        "economics_score": 75.0,
    }
    new_scores = {
        "quality_score": 75.0,
        "reliability_score": 70.0,
        "economics_score": 74.0,
    }

    alerts = detect_score_changes(
        db,
        entity_type="cooperative",
        entity_id=coop.id,
        old_scores=old_scores,
        new_scores=new_scores,
        threshold=5.0,
    )

    # Should create alerts for quality_score and reliability_score
    assert len(alerts) == 2
    assert all(a.alert_type == "score_drop" for a in alerts)
    assert any(a.field_name == "quality_score" for a in alerts)
    assert any(a.field_name == "reliability_score" for a in alerts)


def test_detect_score_changes_improvement(db):
    """Test detecting score improvements."""
    coop = Cooperative(name="Test Coop")
    db.add(coop)
    db.commit()

    old_scores = {
        "quality_score": 70.0,
        "reliability_score": 60.0,
        "economics_score": 65.0,
    }
    new_scores = {
        "quality_score": 82.0,
        "reliability_score": 60.0,
        "economics_score": 65.0,
    }

    alerts = detect_score_changes(
        db,
        entity_type="cooperative",
        entity_id=coop.id,
        old_scores=old_scores,
        new_scores=new_scores,
        threshold=5.0,
    )

    assert len(alerts) == 1
    assert alerts[0].alert_type == "score_improvement"
    assert alerts[0].severity == "info"


def test_detect_score_changes_below_threshold(db):
    """Test that small changes below threshold are ignored."""
    coop = Cooperative(name="Test Coop")
    db.add(coop)
    db.commit()

    old_scores = {
        "quality_score": 80.0,
        "reliability_score": 75.0,
        "economics_score": 70.0,
    }
    new_scores = {
        "quality_score": 82.0,
        "reliability_score": 76.0,
        "economics_score": 71.0,
    }

    alerts = detect_score_changes(
        db,
        entity_type="cooperative",
        entity_id=coop.id,
        old_scores=old_scores,
        new_scores=new_scores,
        threshold=5.0,
    )

    assert len(alerts) == 0


def test_detect_score_changes_severity(db):
    """Test severity levels for score drops."""
    coop = Cooperative(name="Test Coop")
    db.add(coop)
    db.commit()

    # Critical drop (>15 points)
    old_scores = {
        "quality_score": 90.0,
        "reliability_score": 80.0,
        "economics_score": 75.0,
    }
    new_scores = {
        "quality_score": 70.0,
        "reliability_score": 80.0,
        "economics_score": 75.0,
    }

    alerts = detect_score_changes(
        db,
        entity_type="cooperative",
        entity_id=coop.id,
        old_scores=old_scores,
        new_scores=new_scores,
        threshold=5.0,
    )

    assert len(alerts) == 1
    assert alerts[0].severity == "critical"


def test_detect_certification_changes_added(db):
    """Test detecting new certifications."""
    coop = Cooperative(name="Test Coop")
    db.add(coop)
    db.commit()

    old_certs = "Organic"
    new_certs = "Organic, Fair Trade"

    alerts = detect_certification_changes(
        db,
        entity_type="cooperative",
        entity_id=coop.id,
        old_certs=old_certs,
        new_certs=new_certs,
    )

    assert len(alerts) == 1
    assert alerts[0].alert_type == "new_certification"
    assert alerts[0].severity == "info"


def test_detect_certification_changes_lost(db):
    """Test detecting lost certifications."""
    coop = Cooperative(name="Test Coop")
    db.add(coop)
    db.commit()

    old_certs = "Organic, Fair Trade, Rainforest Alliance"
    new_certs = "Organic, Fair Trade"

    alerts = detect_certification_changes(
        db,
        entity_type="cooperative",
        entity_id=coop.id,
        old_certs=old_certs,
        new_certs=new_certs,
    )

    assert len(alerts) == 1
    assert alerts[0].alert_type == "certification_lost"
    assert alerts[0].severity == "warning"


def test_get_alerts_with_filters(db):
    """Test retrieving alerts with filters."""
    coop = Cooperative(name="Test Coop")
    db.add(coop)
    db.commit()

    # Create some alerts
    alert1 = QualityAlert(
        entity_type="cooperative",
        entity_id=coop.id,
        alert_type="score_drop",
        severity="critical",
        acknowledged=False,
    )
    alert2 = QualityAlert(
        entity_type="cooperative",
        entity_id=coop.id,
        alert_type="score_improvement",
        severity="info",
        acknowledged=True,
    )
    db.add_all([alert1, alert2])
    db.commit()

    # Get unacknowledged alerts
    unack_alerts = get_alerts(db, acknowledged=False)
    assert len(unack_alerts) == 1
    assert unack_alerts[0].severity == "critical"

    # Get critical alerts
    critical_alerts = get_alerts(db, severity="critical")
    assert len(critical_alerts) == 1


def test_get_alert_summary(db):
    """Test alert summary statistics."""
    coop = Cooperative(name="Test Coop")
    db.add(coop)
    db.commit()

    # Create alerts with different severities
    alerts = [
        QualityAlert(
            entity_type="cooperative",
            entity_id=coop.id,
            alert_type="score_drop",
            severity="critical",
            acknowledged=False,
        ),
        QualityAlert(
            entity_type="cooperative",
            entity_id=coop.id,
            alert_type="score_drop",
            severity="warning",
            acknowledged=False,
        ),
        QualityAlert(
            entity_type="cooperative",
            entity_id=coop.id,
            alert_type="score_improvement",
            severity="info",
            acknowledged=True,
        ),
    ]
    db.add_all(alerts)
    db.commit()

    summary = get_alert_summary(db)

    assert summary["total_alerts"] == 3
    assert summary["unacknowledged"] == 2
    assert summary["by_severity"]["critical"] == 1
    assert summary["by_severity"]["warning"] == 1
    assert summary["by_severity"]["info"] == 1


def test_acknowledge_alert(db):
    """Test acknowledging an alert."""
    coop = Cooperative(name="Test Coop")
    db.add(coop)
    db.commit()

    alert = QualityAlert(
        entity_type="cooperative",
        entity_id=coop.id,
        alert_type="score_drop",
        severity="warning",
        acknowledged=False,
    )
    db.add(alert)
    db.commit()
    alert_id = alert.id

    # Acknowledge the alert
    ack_alert = acknowledge_alert(db, alert_id=alert_id, acknowledged_by="test_user")

    assert ack_alert is not None
    assert ack_alert.acknowledged is True
    assert ack_alert.acknowledged_by == "test_user"
    assert ack_alert.acknowledged_at is not None
