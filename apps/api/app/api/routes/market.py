import json

import redis as redis_lib
import redis.asyncio as aioredis
import structlog
from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.orm import Session

from celery.result import AsyncResult

from app.api.deps import require_role
from app.api.response_utils import apply_create_status
from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db, SessionLocal
from app.models.market import MarketObservation
from app.models.user import User
from app.schemas.market import MarketObservationCreate, MarketObservationOut
from app.workers.celery_app import celery
from app.core.audit import AuditLogger

log = structlog.get_logger()
router = APIRouter()


@router.get("/observations", response_model=list[MarketObservationOut])
def list_observations(
    key: str | None = None,
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    q = db.query(MarketObservation)
    if key:
        q = q.filter(MarketObservation.key == key)
    return q.order_by(MarketObservation.observed_at.desc()).limit(limit).all()


@router.post("/observations", response_model=MarketObservationOut)
def create_observation(
    payload: MarketObservationCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "analyst")),
):
    obs = MarketObservation(**payload.model_dump())
    db.add(obs)
    db.commit()
    db.refresh(obs)

    # Log creation for audit trail
    AuditLogger.log_create(
        db=db,
        user=user,
        entity_type="market_observation",
        entity_id=obs.id,
        entity_data=payload.model_dump(),
    )

    apply_create_status(request, response, created=True)

    return obs


@router.get("/latest")
def latest_snapshot(
    db: Session = Depends(get_db), _=Depends(require_role("admin", "analyst", "viewer"))
):
    # return latest per key
    keys = ["FX:USD_EUR", "COFFEE_C:USD_LB", "FREIGHT:USD_PER_40FT"]
    out = {}
    for k in keys:
        obs = (
            db.query(MarketObservation)
            .filter(MarketObservation.key == k)
            .order_by(MarketObservation.observed_at.desc())
            .first()
        )
        out[k] = (
            None
            if not obs
            else {
                "value": obs.value,
                "unit": obs.unit,
                "currency": obs.currency,
                "observed_at": obs.observed_at,
            }
        )
    return out


@router.get("/series")
def series(
    key: str,
    limit: int = Query(365, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Return a time series for one key (newest -> oldest)."""
    rows = (
        db.query(MarketObservation)
        .filter(MarketObservation.key == key)
        .order_by(MarketObservation.observed_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "observed_at": r.observed_at,
            "value": r.value,
            "unit": r.unit,
            "currency": r.currency,
        }
        for r in rows
    ]


@router.post("/refresh")
def refresh_market_async(_=Depends(require_role("admin", "analyst"))):
    """Enqueue a market refresh via Celery.

    This mirrors the periodic beat job, but allows manual triggering from the UI.
    """
    res = celery.send_task("app.workers.tasks.refresh_market")
    return {"status": "queued", "task_id": res.id}


@router.get("/tasks/{task_id}")
def market_task_status(
    task_id: str, _=Depends(require_role("admin", "analyst", "viewer"))
):
    r = AsyncResult(task_id, app=celery)
    payload = None
    try:
        payload = r.result if r.ready() else None
    except Exception as exc:
        log.warning("market_task_status_failed", task_id=task_id, error=str(exc))
        payload = None
    return {"task_id": task_id, "state": r.state, "ready": r.ready(), "result": payload}


@router.get("/realtime/status")
def realtime_status(_=Depends(require_role("admin", "analyst", "viewer"))):
    """Return whether the realtime price feed is enabled and the last cached price."""
    from app.services.price_stream import get_cached_price

    enabled = getattr(settings, "REALTIME_PRICE_FEED_ENABLED", False)
    cached: dict | None = None
    redis_error: str | None = None

    if enabled:
        try:
            r = redis_lib.from_url(settings.REDIS_URL)
            cached = get_cached_price(r)
            r.close()
        except Exception as e:
            redis_error = str(e)
            log.warning("realtime_status_redis_error", error=redis_error)

    return {
        "realtime_enabled": enabled,
        "cached_price": cached,
        **({"redis_error": redis_error} if redis_error else {}),
    }


@router.websocket("/ws/price")
async def websocket_price(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    """WebSocket endpoint that streams realtime coffee price updates.

    Authentication: pass the JWT as ``?token=<JWT>`` query parameter.
    Note: passing credentials in query params is a known limitation of the
    WebSocket protocol (``Authorization`` headers are not supported in browser
    WebSocket APIs).  Consider the token short-lived and treat the connection
    URL as a secret.

    The endpoint is only active when ``REALTIME_PRICE_FEED_ENABLED=true``.
    When the feature flag is off, the connection is immediately closed with
    code 1008 (Policy Violation).

    On connection the current cached price is sent immediately, followed by
    live updates as they are published to the Redis Pub/Sub channel.
    """
    if not getattr(settings, "REALTIME_PRICE_FEED_ENABLED", False):
        await websocket.close(code=1008, reason="Realtime feed disabled")
        return

    # --- Authentication & authorisation ---
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return
    try:
        payload = decode_token(token)  # raises on invalid/expired tokens
    except Exception:
        await websocket.close(code=1008, reason="Invalid token")
        return

    user_email = payload.get("sub") if isinstance(payload, dict) else None
    if not user_email:
        await websocket.close(code=1008, reason="Invalid token payload")
        return

    # Look up the user in the database and enforce is_active and role checks
    # (same rules as the /market/latest REST endpoint)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == user_email).first()
    finally:
        db.close()

    if user is None or not getattr(user, "is_active", False):
        await websocket.close(code=1008, reason="Inactive or unknown user")
        return

    allowed_roles = {"admin", "analyst", "viewer"}
    if getattr(user, "role", None) not in allowed_roles:
        await websocket.close(code=1008, reason="Insufficient role")
        return

    await websocket.accept()

    from app.services.price_stream import (
        REDIS_CHANNEL,
        get_cached_price,
    )

    # Use the synchronous client only for the initial cache read,
    # then switch to redis.asyncio for the non-blocking Pub/Sub loop.
    sync_redis = redis_lib.from_url(settings.REDIS_URL)
    cached = get_cached_price(sync_redis)
    sync_redis.close()

    if cached:
        try:
            await websocket.send_text(json.dumps(cached))
        except Exception:
            return

    # True async Pub/Sub – no thread-pool overhead per connection
    async_redis = aioredis.from_url(settings.REDIS_URL)
    pubsub = async_redis.pubsub()
    await pubsub.subscribe(REDIS_CHANNEL)

    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            data = message["data"]
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            await websocket.send_text(data)
    except WebSocketDisconnect:
        log.info("ws_price_disconnect")
    except Exception as exc:
        log.warning("ws_price_error", error=str(exc))
    finally:
        await pubsub.unsubscribe(REDIS_CHANNEL)
        await pubsub.aclose()
        await async_redis.aclose()
