"""Compatibility wrapper for data-health routes.

Canonical implementation lives in app.domains.health.api.data_health_routes.
"""

from app.domains.health.api.data_health_routes import (
    DataFreshnessMonitor,
    DataPipelineOrchestrator,
    _get_redis,
    router,
)

__all__ = ["router", "_get_redis", "DataPipelineOrchestrator", "DataFreshnessMonitor"]