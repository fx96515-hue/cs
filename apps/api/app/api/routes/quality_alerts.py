"""Compatibility wrapper for quality-alert routes.

Canonical implementation lives in app.domains.quality_alerts.api.routes.
"""

from app.domains.quality_alerts.api.routes import anomalies_router, router, settings

__all__ = ["router", "anomalies_router", "settings"]
