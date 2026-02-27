"""Schemas for quality alerts."""

from datetime import datetime
from pydantic import BaseModel


class QualityAlertOut(BaseModel):
    """Quality alert output schema."""

    id: int
    entity_type: str
    entity_id: int
    alert_type: str
    field_name: str | None
    old_value: float | None
    new_value: float | None
    change_amount: float | None
    severity: str
    acknowledged: bool
    acknowledged_by: str | None
    acknowledged_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertSummaryOut(BaseModel):
    """Alert summary statistics."""

    total_alerts: int
    unacknowledged: int
    by_severity: dict[str, int]


class AcknowledgeAlertIn(BaseModel):
    """Request to acknowledge an alert."""

    acknowledged_by: str


class CheckAlertsOut(BaseModel):
    """Response from checking alerts."""

    status: str
    alerts_created: int
    cooperatives_checked: int
    roasters_checked: int


class AnomalyScanOut(BaseModel):
    """Response from running an anomaly scan."""

    status: str
    score_anomalies_detected: int
    price_anomalies_detected: int
    total_anomalies: int
