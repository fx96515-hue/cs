from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis as redis_lib
import structlog

from app.core.config import settings
from app.db.session import get_db

router = APIRouter()
log = structlog.get_logger(__name__)
_SERVICE_ERROR = "error"
_DB_HEALTH_FAILURE = "Database health check failed"
_REDIS_HEALTH_FAILURE = "Redis health check failed"
SERVICE_UNAVAILABLE_RESPONSES: dict[int | str, dict[str, Any]] = {
    503: {"description": "Service unavailable"}
}


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
def ready(
    db: Annotated[Session, Depends(get_db)],
):
    """Readiness endpoint: checks optional dependencies but does not block startup.

    Returns 200 if core app is up and all dependency checks succeed within short timeouts,
    otherwise 503 with details.
    """
    checks: dict = {"status": "ok", "services": {}}

    # DB check (non-fatal)
    try:
        db.execute(text("SELECT 1")).scalar()
        checks["services"]["database"] = "ok"
    except Exception as exc:
        log.warning("ready_database_check_failed", error=str(exc))
        checks["services"]["database"] = _SERVICE_ERROR

    # Redis check (non-fatal)
    try:
        client = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        try:
            client.ping()
            checks["services"]["redis"] = "ok"
        finally:
            client.close()
    except Exception as exc:
        log.warning("ready_redis_check_failed", error=str(exc))
        checks["services"]["redis"] = _SERVICE_ERROR

    # overall status
    overall_ok = all(v == "ok" for v in checks["services"].values())
    return JSONResponse(status_code=(200 if overall_ok else 503), content=checks)


@router.get("/health/db", responses=SERVICE_UNAVAILABLE_RESPONSES)
def health_db(db: Annotated[Session, Depends(get_db)]):
    """Check database connectivity."""
    try:
        db.execute(text("SELECT 1")).scalar()
        return {"status": "ok", "service": "database"}
    except Exception as exc:
        log.warning("health_db_failed", error=str(exc))
        raise HTTPException(status_code=503, detail=_DB_HEALTH_FAILURE) from None


@router.get("/health/redis", responses=SERVICE_UNAVAILABLE_RESPONSES)
def health_redis():
    """Check Redis connectivity."""
    try:
        client = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        try:
            client.ping()
        finally:
            client.close()
        return {"status": "ok", "service": "redis"}
    except Exception as exc:
        log.warning("health_redis_failed", error=str(exc))
        raise HTTPException(status_code=503, detail=_REDIS_HEALTH_FAILURE) from None
