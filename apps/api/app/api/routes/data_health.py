"""Data health monitoring and control endpoints.

Provides visibility into data freshness, circuit breaker status,
and manual pipeline triggers.
"""

from fastapi import APIRouter, Depends
import redis
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services.data_pipeline.freshness import DataFreshnessMonitor
from app.services.data_pipeline.orchestrator import DataPipelineOrchestrator

router = APIRouter()


def _get_redis() -> redis.Redis:
    """Get Redis connection."""
    return redis.from_url(settings.REDIS_URL)


@router.get("/status")
def data_health_status(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Return freshness status of all data sources.

    Returns comprehensive status including:
    - Last update timestamp for each data category
    - Age in hours
    - Staleness flag
    - Overall health status
    """
    monitor = DataFreshnessMonitor(db)
    report = monitor.get_freshness_report()
    return report


@router.get("/sources")
def list_data_sources(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """List all configured data sources and their circuit breaker status.

    Returns:
    - Circuit breaker state for each provider
    - Failure counts
    - Last failure timestamp
    """
    redis_client = _get_redis()
    try:
        orchestrator = DataPipelineOrchestrator(db, redis_client)
        circuit_status = orchestrator.get_circuit_breaker_status()

        return {
            "sources": circuit_status,
            "note": (
                "Circuit breaker states: closed=healthy, open=failing, "
                "half_open=testing recovery"
            ),
        }
    finally:
        redis_client.close()


@router.post("/refresh-all")
def trigger_full_refresh(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "analyst")),
):
    """Trigger complete data pipeline refresh.

    Enqueues a background task that runs:
    1. FX rates refresh (all sources with fallback)
    2. Coffee prices refresh (all sources with fallback)
    3. Peru weather data
    4. News refresh
    5. Cooperative scoring update

    Returns task ID for status tracking.
    """
    redis_client = _get_redis()
    try:
        orchestrator = DataPipelineOrchestrator(db, redis_client)

        # Run synchronously for immediate feedback
        # (Could also enqueue as Celery task for async execution)
        result = orchestrator.run_full_pipeline()

        return {
            "status": result.status,
            "duration_seconds": result.duration_seconds,
            "operations": result.operations,
            "errors": result.errors,
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat(),
        }
    finally:
        redis_client.close()


@router.post("/refresh-market")
def trigger_market_refresh(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "analyst")),
):
    """Trigger market data refresh only (FX + coffee prices).

    Faster than full refresh, only updates market observations.
    """
    redis_client = _get_redis()
    try:
        orchestrator = DataPipelineOrchestrator(db, redis_client)
        result = orchestrator.run_market_pipeline()

        return {
            "status": result["status"],
            "duration_seconds": result["duration_seconds"],
            "results": result["results"],
            "errors": result["errors"],
        }
    finally:
        redis_client.close()


@router.post("/refresh-intelligence")
def trigger_intelligence_refresh(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "analyst")),
):
    """Trigger intelligence pipeline refresh (Peru weather + news).

    Updates regional intelligence without touching market data.
    """
    redis_client = _get_redis()
    try:
        orchestrator = DataPipelineOrchestrator(db, redis_client)
        result = orchestrator.run_intelligence_pipeline()

        return {
            "status": result["status"],
            "duration_seconds": result["duration_seconds"],
            "results": result["results"],
            "errors": result["errors"],
        }
    finally:
        redis_client.close()


@router.post("/reset-circuit/{provider}")
def reset_circuit_breaker(
    provider: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Reset a circuit breaker to closed state.

    Use this to manually recover from a circuit breaker that's stuck open.

    Args:
        provider: Provider name (fx_rates, coffee_prices, peru_weather, etc.)
    """
    redis_client = _get_redis()
    try:
        orchestrator = DataPipelineOrchestrator(db, redis_client)

        if provider not in orchestrator.breakers:
            return {
                "error": f"Unknown provider: {provider}",
                "available_providers": list(orchestrator.breakers.keys()),
            }

        breaker = orchestrator.breakers[provider]
        old_status = breaker.get_status()
        breaker.reset()
        new_status = breaker.get_status()

        return {
            "provider": provider,
            "old_state": old_status["state"],
            "new_state": new_status["state"],
            "message": f"Circuit breaker for {provider} reset to closed state",
        }
    finally:
        redis_client.close()
