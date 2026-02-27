"""Quality alerts API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role, get_db
from app.core.config import settings
from app.schemas.quality_alerts import (
    QualityAlertOut,
    AlertSummaryOut,
    AcknowledgeAlertIn,
    CheckAlertsOut,
    AnomalyScanOut,
)
from app.services import quality_alerts


router = APIRouter()
anomalies_router = APIRouter()


def _require_anomaly_detection_enabled() -> None:
    """Raise 503 when the anomaly-detection feature flag is off."""
    if not settings.ANOMALY_DETECTION_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Anomaly detection is disabled (ANOMALY_DETECTION_ENABLED=false).",
        )


@router.get("", response_model=list[QualityAlertOut])
def list_alerts(
    entity_type: str | None = None,
    severity: str | None = None,
    acknowledged: bool | None = None,
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    """List quality alerts with optional filters."""
    alerts = quality_alerts.get_alerts(
        db,
        entity_type=entity_type,
        severity=severity,
        acknowledged=acknowledged,
        limit=limit,
        offset=offset,
    )
    return alerts


@router.get("/summary", response_model=AlertSummaryOut)
def get_summary(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    """Get alert summary statistics."""
    return quality_alerts.get_alert_summary(db)


@router.post("/{alert_id}/acknowledge", response_model=QualityAlertOut)
def acknowledge_alert(
    alert_id: int,
    payload: AcknowledgeAlertIn,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    """Acknowledge an alert."""
    alert = quality_alerts.acknowledge_alert(
        db, alert_id=alert_id, acknowledged_by=payload.acknowledged_by
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/check-now", response_model=CheckAlertsOut)
def check_now(
    threshold: float = Query(5.0, ge=0.0, le=100.0),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    """Manually trigger alert check."""
    result = quality_alerts.check_all_entities(db, threshold=threshold)
    return result


# ---------------------------------------------------------------------------
# Anomaly Detection endpoints
# ---------------------------------------------------------------------------


@anomalies_router.get("", response_model=list[QualityAlertOut])
def list_anomalies(
    entity_type: str | None = None,
    severity: str | None = None,
    acknowledged: bool | None = None,
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    """List anomaly alerts (Isolation Forest score anomalies and Z-Score price anomalies)."""
    _require_anomaly_detection_enabled()
    from app.services.anomaly_detection import ANOMALY_ALERT_TYPES

    alerts = quality_alerts.get_alerts(
        db,
        entity_type=entity_type,
        severity=severity,
        acknowledged=acknowledged,
        limit=limit,
        offset=offset,
        alert_types=list(ANOMALY_ALERT_TYPES),
    )
    return alerts


@anomalies_router.post("/scan", response_model=AnomalyScanOut)
def run_scan(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    """Manually trigger anomaly scan (Isolation Forest + Z-Score)."""
    _require_anomaly_detection_enabled()
    from app.services.anomaly_detection import run_anomaly_scan

    result = run_anomaly_scan(db)
    return result
