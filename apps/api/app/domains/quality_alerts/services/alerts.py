"""Quality alerts service for monitoring score changes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.quality_alert import QualityAlert
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster


def detect_score_changes(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    old_scores: Mapping[str, float | None],
    new_scores: Mapping[str, float | None],
    threshold: float = 5.0,
) -> list[QualityAlert]:
    """Detect significant score changes and create alerts.

    Args:
        db: Database session
        entity_type: 'cooperative' or 'roaster'
        entity_id: Entity ID
        old_scores: Old score values (quality_score, reliability_score, economics_score)
        new_scores: New score values
        threshold: Minimum change to trigger alert

    Returns:
        List of created QualityAlert instances
    """
    alerts = []
    score_fields = ["quality_score", "reliability_score", "economics_score"]

    for field in score_fields:
        old_val = old_scores.get(field)
        new_val = new_scores.get(field)

        # Skip if either value is None
        if old_val is None or new_val is None:
            continue

        change = new_val - old_val

        # Skip if change is below threshold
        if abs(change) < threshold:
            continue

        # Determine alert type and severity
        if change < 0:
            alert_type = "score_drop"
            if abs(change) >= 15:
                severity = "critical"
            elif abs(change) >= 10:
                severity = "warning"
            else:
                severity = "info"
        else:
            alert_type = "score_improvement"
            severity = "info"

        alert = QualityAlert(
            entity_type=entity_type,
            entity_id=entity_id,
            alert_type=alert_type,
            field_name=field,
            old_value=old_val,
            new_value=new_val,
            change_amount=change,
            severity=severity,
            acknowledged=False,
        )
        db.add(alert)
        alerts.append(alert)

    if alerts:
        db.commit()

    return alerts


def detect_certification_changes(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    old_certs: str | None,
    new_certs: str | None,
) -> list[QualityAlert]:
    """Detect certification changes and create alerts.

    Args:
        db: Database session
        entity_type: 'cooperative' or 'roaster'
        entity_id: Entity ID
        old_certs: Old certification string
        new_certs: New certification string

    Returns:
        List of created QualityAlert instances
    """
    alerts = []

    # Parse certification strings (comma-separated)
    old_set = set(c.strip().lower() for c in (old_certs or "").split(",") if c.strip())
    new_set = set(c.strip().lower() for c in (new_certs or "").split(",") if c.strip())

    # New certifications
    added = new_set - old_set
    if added:
        alert = QualityAlert(
            entity_type=entity_type,
            entity_id=entity_id,
            alert_type="new_certification",
            field_name="certifications",
            old_value=None,
            new_value=None,
            change_amount=None,
            severity="info",
            acknowledged=False,
        )
        db.add(alert)
        alerts.append(alert)

    # Lost certifications
    removed = old_set - new_set
    if removed:
        alert = QualityAlert(
            entity_type=entity_type,
            entity_id=entity_id,
            alert_type="certification_lost",
            field_name="certifications",
            old_value=None,
            new_value=None,
            change_amount=None,
            severity="warning",
            acknowledged=False,
        )
        db.add(alert)
        alerts.append(alert)

    if alerts:
        db.commit()

    return alerts


def check_all_entities(db: Session, *, threshold: float = 5.0) -> dict[str, Any]:
    """Check all entities for quality alerts.

    This compares current scores with previous scores stored in meta.

    Args:
        db: Database session
        threshold: Minimum score change to trigger alert

    Returns:
        Summary dict with counts
    """
    alerts_created = 0

    # Check cooperatives
    cooperatives = db.query(Cooperative).all()
    for coop in cooperatives:
        # Get previous scores from meta
        meta = coop.meta or {}
        previous_scores = meta.get("previous_scores", {})

        current_scores = {
            "quality_score": coop.quality_score,
            "reliability_score": coop.reliability_score,
            "economics_score": coop.economics_score,
        }

        if previous_scores:
            alerts = detect_score_changes(
                db,
                entity_type="cooperative",
                entity_id=coop.id,
                old_scores=previous_scores,
                new_scores=current_scores,
                threshold=threshold,
            )
            alerts_created += len(alerts)

    # Check roasters
    roasters = db.query(Roaster).all()
    for roaster in roasters:
        meta = roaster.meta or {}
        previous_scores = meta.get("previous_scores", {})

        # Roasters don't have individual score fields, use getattr with None defaults
        current_scores = {
            "quality_score": getattr(roaster, "quality_score", None),
            "reliability_score": getattr(roaster, "reliability_score", None),
            "economics_score": getattr(roaster, "economics_score", None),
        }

        if previous_scores:
            alerts = detect_score_changes(
                db,
                entity_type="roaster",
                entity_id=roaster.id,
                old_scores=previous_scores,
                new_scores=current_scores,
                threshold=threshold,
            )
            alerts_created += len(alerts)

    return {
        "status": "ok",
        "alerts_created": alerts_created,
        "cooperatives_checked": len(cooperatives),
        "roasters_checked": len(roasters),
    }


def get_alerts(
    db: Session,
    *,
    entity_type: str | None = None,
    severity: str | None = None,
    acknowledged: bool | None = None,
    alert_types: list[str] | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[QualityAlert]:
    """Get alerts with filters.

    Args:
        db: Database session
        entity_type: Filter by entity type
        severity: Filter by severity
        acknowledged: Filter by acknowledged status
        alert_types: Filter to specific alert type values (e.g. anomaly types)
        limit: Max results
        offset: Offset for pagination

    Returns:
        List of QualityAlert instances
    """
    stmt = select(QualityAlert).order_by(QualityAlert.created_at.desc())

    if entity_type:
        stmt = stmt.where(QualityAlert.entity_type == entity_type)
    if severity:
        stmt = stmt.where(QualityAlert.severity == severity)
    if acknowledged is not None:
        stmt = stmt.where(QualityAlert.acknowledged == acknowledged)
    if alert_types is not None:
        stmt = stmt.where(QualityAlert.alert_type.in_(alert_types))

    stmt = stmt.limit(limit).offset(offset)

    result = db.execute(stmt)
    return list(result.scalars().all())


def get_alert_summary(db: Session) -> dict[str, Any]:
    """Get alert summary statistics.

    Returns:
        Dict with counts by severity and acknowledgment status
    """
    total = db.query(QualityAlert).count()
    unacknowledged = (
        db.query(QualityAlert).filter(QualityAlert.acknowledged.is_(False)).count()
    )

    critical = (
        db.query(QualityAlert).filter(QualityAlert.severity == "critical").count()
    )
    warning = db.query(QualityAlert).filter(QualityAlert.severity == "warning").count()
    info = db.query(QualityAlert).filter(QualityAlert.severity == "info").count()

    return {
        "total_alerts": total,
        "unacknowledged": unacknowledged,
        "by_severity": {
            "critical": critical,
            "warning": warning,
            "info": info,
        },
    }


def acknowledge_alert(
    db: Session, *, alert_id: int, acknowledged_by: str
) -> QualityAlert | None:
    """Acknowledge an alert.

    Args:
        db: Database session
        alert_id: Alert ID
        acknowledged_by: Username or identifier

    Returns:
        Updated QualityAlert or None if not found
    """
    alert = db.get(QualityAlert, alert_id)
    if not alert:
        return None

    alert.acknowledged = True
    alert.acknowledged_by = acknowledged_by
    alert.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)

    return alert


def detect_price_volatility(
    db: Session,
    *,
    threshold_pct: float = 5.0,
) -> list[QualityAlert]:
    """Detect significant Coffee C price swings over the last 24 hours.

    Compares the latest ``COFFEE_C:USD_LB`` market observation against the
    oldest observation recorded within the last 24 h.  If the relative change
    exceeds *threshold_pct* (default 5 %) a ``QualityAlert`` of
    ``entity_type="market"`` (``entity_id=0``) is created.

    Args:
        db: Database session.
        threshold_pct: Minimum percentage change to trigger an alert.

    Returns:
        List of newly created QualityAlert instances (empty when no alert fired).
    """
    from app.models.market import MarketObservation

    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)

    # Latest observation (most recent price)
    latest_obs = (
        db.query(MarketObservation)
        .filter(
            MarketObservation.key == "COFFEE_C:USD_LB",
            MarketObservation.observed_at >= since,
        )
        .order_by(MarketObservation.observed_at.desc())
        .first()
    )

    # Oldest observation in the window (24 h ago baseline)
    oldest_obs = (
        db.query(MarketObservation)
        .filter(
            MarketObservation.key == "COFFEE_C:USD_LB",
            MarketObservation.observed_at >= since,
        )
        .order_by(MarketObservation.observed_at.asc())
        .first()
    )

    if not latest_obs or not oldest_obs or latest_obs.id == oldest_obs.id:
        # Need at least two data points
        return []

    old_price = oldest_obs.value
    new_price = latest_obs.value

    if old_price == 0:
        return []

    change_pct = ((new_price - old_price) / old_price) * 100.0

    if abs(change_pct) < threshold_pct:
        return []

    # Determine severity
    if abs(change_pct) >= 10.0:
        severity = "critical"
    elif abs(change_pct) >= 7.5:
        severity = "warning"
    else:
        severity = "info"

    alert = QualityAlert(
        entity_type="market",
        entity_id=0,
        alert_type="price_volatility",
        field_name="COFFEE_C:USD_LB",
        old_value=old_price,
        new_value=new_price,
        change_amount=change_pct,
        severity=severity,
        acknowledged=False,
    )
    db.add(alert)
    db.commit()

    return [alert]
