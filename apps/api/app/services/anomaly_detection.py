"""Anomaly detection service for entity scores and market prices.

Implements:
- Isolation Forest for entity score outliers
- Z-Score for market price anomalies

Detected anomalies are stored as QualityAlert records with
alert_type 'score_anomaly' or 'price_anomaly'.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np
import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cooperative import Cooperative
from app.models.market import MarketObservation
from app.models.quality_alert import QualityAlert

try:
    from sklearn.ensemble import IsolationForest
except ImportError:  # pragma: no cover
    IsolationForest = None

log = structlog.get_logger()

ANOMALY_ALERT_TYPES = frozenset({"score_anomaly", "price_anomaly"})

# Minimum number of entities required for Isolation Forest
_MIN_ENTITIES_FOR_IF = 10

# Minimum number of price observations required for Z-Score (excluding the latest)
_MIN_OBS_FOR_ZSCORE = 3

# Maximum historical observations per market key for the Z-Score baseline
_MAX_OBS_PER_KEY = 200


def _existing_unacknowledged(
    db: Session,
    entity_type: str,
    entity_id: int,
    alert_type: str,
    field_name: str | None,
) -> bool:
    """Return True if an unacknowledged anomaly alert already exists."""
    stmt = select(QualityAlert).where(
        QualityAlert.entity_type == entity_type,
        QualityAlert.entity_id == entity_id,
        QualityAlert.alert_type == alert_type,
        QualityAlert.acknowledged.is_(False),
    )
    if field_name is not None:
        stmt = stmt.where(QualityAlert.field_name == field_name)
    return db.execute(stmt).first() is not None


def detect_score_anomalies(db: Session) -> list[QualityAlert]:
    """Detect cooperative score outliers using Isolation Forest.

    Collects all cooperative score vectors (quality_score, reliability_score,
    economics_score) and flags statistical outliers.  Only cooperatives are
    used because Roaster does not expose the three individual score fields.

    Requires at least 10 cooperatives with all three scores set.

    Returns:
        List of newly created QualityAlert instances (alert_type='score_anomaly').
    """
    if IsolationForest is None:  # pragma: no cover
        log.warning("sklearn_unavailable", reason="skipping score anomaly detection")
        return []

    # Collect (entity_type, entity_id, q, r, e) tuples – cooperatives only
    entities: list[tuple[str, int, float, float, float]] = []

    for coop in db.query(Cooperative).all():
        q, r, e = coop.quality_score, coop.reliability_score, coop.economics_score
        if q is not None and r is not None and e is not None:
            entities.append(("cooperative", coop.id, float(q), float(r), float(e)))

    if len(entities) < _MIN_ENTITIES_FOR_IF:
        log.info(
            "score_anomaly_detection_skipped",
            reason="insufficient_data",
            count=len(entities),
            minimum=_MIN_ENTITIES_FOR_IF,
        )
        return []

    X = np.array([[e[2], e[3], e[4]] for e in entities], dtype=float)

    clf = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
    clf.fit(X)
    preds = clf.predict(X)  # -1 = outlier, 1 = inlier
    scores = clf.score_samples(X)  # lower = more anomalous

    alerts: list[QualityAlert] = []
    for idx, pred in enumerate(preds):
        if pred != -1:
            continue

        entity_type, entity_id, q, r, e = entities[idx]
        anomaly_score = float(scores[idx])

        # Skip if an open anomaly alert already exists for this entity
        if _existing_unacknowledged(
            db, entity_type, entity_id, "score_anomaly", "scores"
        ):
            continue

        severity = "critical" if anomaly_score < -0.1 else "warning"
        mean_score = float(np.mean([q, r, e]))

        alert = QualityAlert(
            entity_type=entity_type,
            entity_id=entity_id,
            alert_type="score_anomaly",
            field_name="scores",
            old_value=None,
            new_value=mean_score,
            change_amount=anomaly_score,
            severity=severity,
            acknowledged=False,
        )
        db.add(alert)
        alerts.append(alert)

    if alerts:
        db.commit()

    log.info(
        "score_anomaly_detection_done",
        entities_checked=len(entities),
        anomalies_found=len(alerts),
    )
    return alerts


def detect_price_anomalies(
    db: Session, *, z_threshold: float = 3.0
) -> list[QualityAlert]:
    """Detect market price anomalies using the Z-Score method.

    Fetches recent observations for all market keys in a single query,
    groups them in Python, and for each key evaluates whether the latest
    observation is an outlier relative to the historical baseline (excluding
    the latest point from the mean/std calculation).

    Args:
        db: Database session.
        z_threshold: Minimum |z-score| to create an alert (default 3.0).

    Returns:
        List of newly created QualityAlert instances (alert_type='price_anomaly').
    """
    # Single query: fetch id, key, value ordered by key then newest-first.
    # We select only the columns needed to avoid loading heavy JSON/text fields.
    raw_rows = (
        db.query(
            MarketObservation.id,
            MarketObservation.key,
            MarketObservation.value,
        )
        .order_by(MarketObservation.key, MarketObservation.observed_at.desc())
        .all()
    )

    # Group into per-key lists, honouring the _MAX_OBS_PER_KEY cap
    obs_by_key: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for obs_id, key, value in raw_rows:
        bucket = obs_by_key[key]
        if len(bucket) < _MAX_OBS_PER_KEY:
            bucket.append((obs_id, value))

    alerts: list[QualityAlert] = []
    for key, bucket in obs_by_key.items():
        # Need the latest + at least _MIN_OBS_FOR_ZSCORE historical points
        if len(bucket) < _MIN_OBS_FOR_ZSCORE + 1:
            continue

        latest_id, latest_value = bucket[0]

        # Compute baseline statistics excluding the latest observation
        baseline_values = np.array([v for _, v in bucket[1:]], dtype=float)
        mean = float(np.mean(baseline_values))
        std = float(np.std(baseline_values))

        if std == 0.0:
            continue

        z = abs((latest_value - mean) / std)

        if z < z_threshold:
            continue

        # Skip if an open alert already exists for this observation
        if _existing_unacknowledged(db, "market", latest_id, "price_anomaly", key):
            continue

        severity = "critical" if z > 5.0 else "warning"

        alert = QualityAlert(
            entity_type="market",
            entity_id=latest_id,
            alert_type="price_anomaly",
            field_name=key,
            old_value=mean,
            new_value=latest_value,
            change_amount=z,
            severity=severity,
            acknowledged=False,
        )
        db.add(alert)
        alerts.append(alert)

    if alerts:
        db.commit()

    log.info(
        "price_anomaly_detection_done",
        keys_checked=len(obs_by_key),
        anomalies_found=len(alerts),
    )
    return alerts


def run_anomaly_scan(db: Session) -> dict[str, Any]:
    """Run a full anomaly scan (entity scores + market prices).

    Returns:
        Summary dict with detection counts and status.
    """
    score_alerts = detect_score_anomalies(db)
    price_alerts = detect_price_anomalies(db)

    return {
        "status": "ok",
        "score_anomalies_detected": len(score_alerts),
        "price_anomalies_detected": len(price_alerts),
        "total_anomalies": len(score_alerts) + len(price_alerts),
    }
