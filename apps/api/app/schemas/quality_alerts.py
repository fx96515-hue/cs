"""Compatibility wrapper for quality-alert schemas.

Canonical implementation lives in app.domains.quality_alerts.schemas.quality_alerts.
"""

from app.domains.quality_alerts.schemas.quality_alerts import (
    AcknowledgeAlertIn,
    AlertSummaryOut,
    AnomalyScanOut,
    CheckAlertsOut,
    QualityAlertOut,
)

__all__ = [
    "QualityAlertOut",
    "AlertSummaryOut",
    "AcknowledgeAlertIn",
    "CheckAlertsOut",
    "AnomalyScanOut",
]
