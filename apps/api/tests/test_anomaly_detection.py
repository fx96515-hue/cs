"""Tests for anomaly detection service."""

from unittest.mock import patch

import pytest

from app.models.cooperative import Cooperative
from app.models.market import MarketObservation
from app.models.quality_alert import QualityAlert
from app.services.anomaly_detection import (
    detect_price_anomalies,
    detect_score_anomalies,
    run_anomaly_scan,
    ANOMALY_ALERT_TYPES,
)
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_coop(db, name: str, q: float, r: float, e: float) -> Cooperative:
    coop = Cooperative(
        name=name,
        quality_score=q,
        reliability_score=r,
        economics_score=e,
    )
    db.add(coop)
    return coop


def _make_obs(db, key: str, value: float, offset_seconds: int = 0) -> MarketObservation:
    from datetime import timedelta

    obs = MarketObservation(
        key=key,
        value=value,
        observed_at=datetime.now(timezone.utc) + timedelta(seconds=offset_seconds),
    )
    db.add(obs)
    return obs


# ---------------------------------------------------------------------------
# detect_score_anomalies – insufficient data
# ---------------------------------------------------------------------------


def test_detect_score_anomalies_insufficient_data(db):
    """Returns empty list when fewer than 10 entities with complete scores."""
    for i in range(5):
        _make_coop(db, f"Coop {i}", 70.0 + i, 65.0 + i, 60.0 + i)
    db.commit()

    alerts = detect_score_anomalies(db)
    assert alerts == []


# ---------------------------------------------------------------------------
# detect_score_anomalies – creates alerts for outliers
# ---------------------------------------------------------------------------


def test_detect_score_anomalies_creates_alerts(db):
    """Creates score_anomaly alerts for outliers when enough data exists."""
    # 9 normal entities with similar scores
    for i in range(9):
        _make_coop(db, f"Normal Coop {i}", 75.0, 72.0, 70.0)
    # 1 extreme outlier
    _make_coop(db, "Outlier Coop", 10.0, 5.0, 3.0)
    db.commit()

    # Mock IsolationForest to always flag entity index 9 as outlier
    import numpy as np

    class _FakeIF:
        def __init__(self, **_kwargs):
            pass

        def fit(self, X):
            return self

        def predict(self, X):
            preds = np.ones(len(X), dtype=int)
            preds[-1] = -1  # last entity is outlier
            return preds

        def score_samples(self, X):
            return np.full(len(X), -0.15)

    with patch("app.services.anomaly_detection.IsolationForest", _FakeIF):
        alerts = detect_score_anomalies(db)

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.alert_type == "score_anomaly"
    assert alert.field_name == "scores"
    assert alert.severity in {"warning", "critical"}


def test_detect_score_anomalies_no_duplicate(db):
    """Does not create a second alert if an unacknowledged one already exists."""
    for i in range(9):
        _make_coop(db, f"Normal {i}", 75.0, 72.0, 70.0)
    outlier = _make_coop(db, "Outlier", 10.0, 5.0, 3.0)
    db.commit()

    # Pre-create an existing open alert for the outlier
    existing = QualityAlert(
        entity_type="cooperative",
        entity_id=outlier.id,
        alert_type="score_anomaly",
        field_name="scores",
        severity="warning",
        acknowledged=False,
    )
    db.add(existing)
    db.commit()

    import numpy as np

    class _FakeIF:
        def __init__(self, **_kwargs):
            pass

        def fit(self, X):
            return self

        def predict(self, X):
            preds = np.ones(len(X), dtype=int)
            preds[-1] = -1
            return preds

        def score_samples(self, X):
            return np.full(len(X), -0.15)

    with patch("app.services.anomaly_detection.IsolationForest", _FakeIF):
        alerts = detect_score_anomalies(db)

    assert len(alerts) == 0


# ---------------------------------------------------------------------------
# detect_price_anomalies
# ---------------------------------------------------------------------------


def test_detect_price_anomalies_insufficient_obs(db):
    """Returns empty list when too few observations exist for a key (needs ≥4 total)."""
    _make_obs(db, "COFFEE_C:USD_LB", 2.50)
    _make_obs(db, "COFFEE_C:USD_LB", 2.52)
    db.commit()

    alerts = detect_price_anomalies(db)
    assert alerts == []


def test_detect_price_anomalies_normal_values(db):
    """Returns no alerts when all values are within normal z-score range."""
    for v in [2.50, 2.51, 2.49, 2.52, 2.48]:
        _make_obs(db, "COFFEE_C:USD_LB", v)
    db.commit()

    alerts = detect_price_anomalies(db)
    assert alerts == []


def test_detect_price_anomalies_creates_alert(db):
    """Creates price_anomaly alert when latest value is a z-score outlier."""
    # 19 stable normal values near 2.50 (+/- tiny noise)
    base_values = [2.50 + (i % 5) * 0.01 for i in range(19)]
    for i, v in enumerate(base_values):
        _make_obs(db, "COFFEE_C:USD_LB", v, offset_seconds=i)
    # Extreme outlier as the most recent observation (well beyond 3 sigma)
    _make_obs(db, "COFFEE_C:USD_LB", 500.0, offset_seconds=100)
    db.commit()

    alerts = detect_price_anomalies(db, z_threshold=3.0)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.alert_type == "price_anomaly"
    assert alert.field_name == "COFFEE_C:USD_LB"
    assert alert.entity_type == "market"
    assert alert.new_value == pytest.approx(500.0)
    assert alert.severity in {"warning", "critical"}


def test_detect_price_anomalies_no_duplicate(db):
    """Does not create a second alert for the same observation."""
    base_values = [2.50 + (i % 5) * 0.01 for i in range(19)]
    for i, v in enumerate(base_values):
        _make_obs(db, "COFFEE_C:USD_LB", v, offset_seconds=i)
    outlier_obs = _make_obs(db, "COFFEE_C:USD_LB", 500.0, offset_seconds=100)
    db.commit()

    # Pre-create existing open alert
    existing = QualityAlert(
        entity_type="market",
        entity_id=outlier_obs.id,
        alert_type="price_anomaly",
        field_name="COFFEE_C:USD_LB",
        severity="critical",
        acknowledged=False,
    )
    db.add(existing)
    db.commit()

    alerts = detect_price_anomalies(db, z_threshold=3.0)
    assert len(alerts) == 0


# ---------------------------------------------------------------------------
# run_anomaly_scan
# ---------------------------------------------------------------------------


def test_run_anomaly_scan_returns_summary(db):
    """run_anomaly_scan returns a summary dict with the expected keys."""
    result = run_anomaly_scan(db)
    assert result["status"] == "ok"
    assert "score_anomalies_detected" in result
    assert "price_anomalies_detected" in result
    assert "total_anomalies" in result
    assert (
        result["total_anomalies"]
        == result["score_anomalies_detected"] + result["price_anomalies_detected"]
    )


# ---------------------------------------------------------------------------
# ANOMALY_ALERT_TYPES constant
# ---------------------------------------------------------------------------


def test_anomaly_alert_types_set():
    assert "score_anomaly" in ANOMALY_ALERT_TYPES
    assert "price_anomaly" in ANOMALY_ALERT_TYPES


# ---------------------------------------------------------------------------
# GET /anomalies endpoint
# ---------------------------------------------------------------------------


def test_get_anomalies_empty(client, auth_headers, db):
    """GET /anomalies returns empty list when no anomaly alerts exist."""
    response = client.get("/anomalies", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_anomalies_only_returns_anomaly_types(client, auth_headers, db):
    """GET /anomalies returns only score_anomaly/price_anomaly alerts."""
    from app.models.cooperative import Cooperative

    coop = Cooperative(name="Test")
    db.add(coop)
    db.commit()

    # Regular score_drop alert (should NOT appear in /anomalies)
    regular = QualityAlert(
        entity_type="cooperative",
        entity_id=coop.id,
        alert_type="score_drop",
        severity="warning",
        acknowledged=False,
    )
    # Anomaly alert (SHOULD appear)
    anomaly = QualityAlert(
        entity_type="cooperative",
        entity_id=coop.id,
        alert_type="score_anomaly",
        field_name="scores",
        severity="warning",
        acknowledged=False,
    )
    db.add_all([regular, anomaly])
    db.commit()

    response = client.get("/anomalies", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["alert_type"] == "score_anomaly"


def test_post_anomalies_scan(client, auth_headers, db):
    """POST /anomalies/scan returns a valid scan summary."""
    response = client.post("/anomalies/scan", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "total_anomalies" in data


def test_get_anomalies_feature_flag_disabled(client, auth_headers, db):
    """GET /anomalies returns 503 when ANOMALY_DETECTION_ENABLED=False."""
    with patch("app.api.routes.quality_alerts.settings") as mock_settings:
        mock_settings.ANOMALY_DETECTION_ENABLED = False
        response = client.get("/anomalies", headers=auth_headers)
    assert response.status_code == 503
    assert "disabled" in response.json()["detail"].lower()


def test_post_anomalies_scan_feature_flag_disabled(client, auth_headers, db):
    """POST /anomalies/scan returns 503 when ANOMALY_DETECTION_ENABLED=False."""
    with patch("app.api.routes.quality_alerts.settings") as mock_settings:
        mock_settings.ANOMALY_DETECTION_ENABLED = False
        response = client.post("/anomalies/scan", headers=auth_headers)
    assert response.status_code == 503
