from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis as redis_lib

from app.core.config import settings
from app.db.session import get_db

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    """Readiness endpoint: checks optional dependencies but does not block startup.

    Returns 200 if core app is up and all dependency checks succeed within short timeouts,
    otherwise 503 with details.
    """
    checks: dict = {"status": "ok", "services": {}}

    # DB check (non-fatal)
    try:
        db.execute(text("SELECT 1")).scalar()
        checks["services"]["database"] = "ok"
    except Exception as e:
        checks["services"]["database"] = f"error: {str(e)}"

    # Redis check (non-fatal)
    try:
        client = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        try:
            client.ping()
            checks["services"]["redis"] = "ok"
        finally:
            client.close()
    except Exception as e:
        checks["services"]["redis"] = f"error: {str(e)}"

    # overall status
    overall_ok = all(v == "ok" for v in checks["services"].values())
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=(200 if overall_ok else 503), content=checks)


@router.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    """Check database connectivity."""
    db.execute(text("SELECT 1")).scalar()
    return {"status": "ok", "service": "database"}


@router.get("/health/redis")
def health_redis():
    """Check Redis connectivity."""
    client = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=2)
    try:
        client.ping()
    finally:
        client.close()
    return {"status": "ok", "service": "redis"}
