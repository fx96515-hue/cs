"""Quality alerts API routes."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role, get_db
from app.core.config import settings
from app.domains.quality_alerts.schemas.quality_alerts import (
    QualityAlertOut,
    AlertSummaryOut,
    AcknowledgeAlertIn,
    CheckAlertsOut,
    AnomalyScanOut,
)
from app.domains.quality_alerts.services import alerts as quality_alerts


router = APIRouter()
anomalies_router = APIRouter()
ENTITY_TYPE_PATTERN = r"^[a-z][a-z0-9_]{1,31}$"
AlertSeverity = Literal["info", "warning", "critical"]
DbSessionDep = Annotated[Session, Depends(get_db)]
AnalystPermissionDep = Annotated[None, Depends(require_role("admin", "analyst"))]
AdminPermissionDep = Annotated[None, Depends(require_role("admin"))]


def _require_anomaly_detection_enabled() -> None:
    """Raise 503 when the anomaly-detection feature flag is off."""
    if not settings.ANOMALY_DETECTION_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Anomaly detection is disabled (ANOMALY_DETECTION_ENABLED=false).",
        )


@router.get("", response_model=list[QualityAlertOut])
def list_alerts(
    db: DbSessionDep,
    _: AnalystPermissionDep,
    entity_type: Annotated[str | None, Query(pattern=ENTITY_TYPE_PATTERN)] = None,
    severity: AlertSeverity | None = None,
    acknowledged: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
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
    db: DbSessionDep,
    _: AnalystPermissionDep,
):
    """Get alert summary statistics."""
    return quality_alerts.get_alert_summary(db)


@router.post(
    "/{alert_id}/acknowledge",
    response_model=QualityAlertOut,
    responses={404: {"description": "Alert not found"}},
)
def acknowledge_alert(
    alert_id: Annotated[int, Path(ge=1)],
    payload: AcknowledgeAlertIn,
    db: DbSessionDep,
    _: AnalystPermissionDep,
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
    db: DbSessionDep,
    _: AdminPermissionDep,
    threshold: Annotated[float, Query(ge=0.0, le=100.0)] = 5.0,
):
    """Manually trigger alert check."""
    result = quality_alerts.check_all_entities(db, threshold=threshold)
    return result


# ---------------------------------------------------------------------------
# Anomaly Detection endpoints
# ---------------------------------------------------------------------------


@anomalies_router.get(
    "",
    response_model=list[QualityAlertOut],
    responses={503: {"description": "Anomaly detection feature is disabled"}},
)
def list_anomalies(
    db: DbSessionDep,
    _: AnalystPermissionDep,
    entity_type: Annotated[str | None, Query(pattern=ENTITY_TYPE_PATTERN)] = None,
    severity: AlertSeverity | None = None,
    acknowledged: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
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


@anomalies_router.post(
    "/scan",
    response_model=AnomalyScanOut,
    responses={503: {"description": "Anomaly detection feature is disabled"}},
)
def run_scan(
    db: DbSessionDep,
    _: AdminPermissionDep,
):
    """Manually trigger anomaly scan (Isolation Forest + Z-Score)."""
    _require_anomaly_detection_enabled()
    from app.services.anomaly_detection import run_anomaly_scan

    result = run_anomaly_scan(db)
    return result
