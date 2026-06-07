"""Compatibility wrapper for quality-alert service.

Canonical implementation lives in app.domains.quality_alerts.services.alerts.
"""

from app.domains.quality_alerts.services.alerts import (
    acknowledge_alert,
    check_all_entities,
    detect_certification_changes,
    detect_price_volatility,
    detect_score_changes,
    get_alert_summary,
    get_alerts,
)

__all__ = [
    "detect_score_changes",
    "detect_certification_changes",
    "check_all_entities",
    "get_alerts",
    "get_alert_summary",
    "acknowledge_alert",
    "detect_price_volatility",
]
