from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, TypedDict

import redis
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.config import settings
from app.db.session import get_db
from app.services.data_pipeline.freshness import DataFreshnessMonitor
from app.services.data_pipeline.orchestrator import DataPipelineOrchestrator
from app.services.data_pipeline.phase2_orchestrator import Phase2DataPipelineFacade

router = APIRouter()


class PipelineSourceDef(TypedDict):
    name: str
    provider: str
    breaker: str | None
    category: str
    item: str


PIPELINE_TRIGGER_ALIASES: dict[str, str] = {
    "fx rates": "market",
    "coffee prices": "market",
    "freight rates": "market",
    "peru weather": "intelligence",
    "market news": "intelligence",
}


def _redact_error_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        redacted: dict[str, Any] = {}
        for key, value in payload.items():
            if key == "errors" and isinstance(value, list):
                redacted[key] = (
                    ["Internal processing error. Check server logs for details."]
                    if value
                    else []
                )
            else:
                redacted[key] = _redact_error_payload(value)
        return redacted
    if isinstance(payload, list):
        return [_redact_error_payload(item) for item in payload]
    return payload


def _get_redis() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL)


def _status_from_breaker(state: str | None) -> str:
    if state == "closed":
        return "online"
    if state == "half_open":
        return "degraded"
    if state == "open":
        return "offline"
    return "unknown"


def _build_pipeline_sources(db: Session) -> list[dict]:
    monitor = DataFreshnessMonitor(db)
    freshness = monitor.get_freshness_report()

    breaker_status: dict = {}
    try:
        redis_client = _get_redis()
        try:
            orchestrator = DataPipelineOrchestrator(db, redis_client)
            breaker_status = orchestrator.get_circuit_breaker_status()
        finally:
            redis_client.close()
    except Exception:
        breaker_status = {}

    def breaker(name: str | None) -> dict:
        if not name:
            return {}
        return breaker_status.get(name, {})

    def latest(category: str, item: str) -> dict:
        return freshness.get("categories", {}).get(category, {}).get(item, {})

    source_defs: list[PipelineSourceDef] = [
        {
            "name": "FX Rates",
            "provider": "ECB / OANDA",
            "breaker": "fx_rates",
            "category": "fx_rates",
            "item": "USD_EUR",
        },
        {
            "name": "Coffee Prices",
            "provider": "Yahoo Finance / Stooq",
            "breaker": "coffee_prices",
            "category": "coffee_prices",
            "item": "COFFEE_C",
        },
        {
            "name": "Peru Weather",
            "provider": "OpenMeteo",
            "breaker": "peru_weather",
            "category": "weather",
            "item": "Cajamarca",
        },
        {
            "name": "Market News",
            "provider": "News Pipeline",
            "breaker": "news",
            "category": "news",
            "item": "latest",
        },
        {
            "name": "Freight Rates",
            "provider": "Market Observations",
            "breaker": "fx_rates",
            "category": "freight_rates",
            "item": "CALLAO_HAMBURG",
        },
        {
            "name": "Shipping Intelligence",
            "provider": "AIS Stream / MarineTraffic",
            "breaker": None,
            "category": "shipments",
            "item": "latest",
        },
        {
            "name": "Peru Macro",
            "provider": "INEI / WITS / BCRP / ICO",
            "breaker": None,
            "category": "macro",
            "item": "latest",
        },
    ]

    rows: list[dict[str, Any]] = []
    for definition in source_defs:
        current_breaker = breaker(definition["breaker"])
        current_latest = latest(definition["category"], definition["item"])
        age_hours = float(current_latest.get("age_hours", 0) or 0)
        errors = int(current_breaker.get("failure_count", 0) or 0)
        rows.append(
            {
                "name": definition["name"],
                "provider": definition["provider"],
                "status": _status_from_breaker(current_breaker.get("state")),
                "lastSync": current_latest.get("last_updated") or "n/a",
                "recordCount": 1 if current_latest else 0,
                "avgLatency": int(age_hours * 10) if current_latest else 0,
                "errorRate": round(min(errors * 5.0, 100.0), 1),
            }
        )

    return rows


@router.get("/sources")
def pipeline_sources(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    return _build_pipeline_sources(db)


@router.get("/status")
def pipeline_status(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    sources = _build_pipeline_sources(db)
    now = datetime.now(timezone.utc)
    online = sum(1 for source in sources if source["status"] == "online")
    degraded = sum(1 for source in sources if source["status"] == "degraded")
    offline = sum(1 for source in sources if source["status"] == "offline")
    return {
        "totalSources": len(sources),
        "online": online,
        "degraded": degraded,
        "offline": offline,
        "lastFullSync": now.isoformat(),
        "nextScheduled": "Configured via Celery Beat",
        "providerCatalog": Phase2DataPipelineFacade.provider_summary(),
    }


@router.post("/trigger-all")
def trigger_all_sources(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
):
    redis_client = _get_redis()
    try:
        orchestrator = DataPipelineOrchestrator(db, redis_client)
        result = orchestrator.run_full_pipeline()
        return {
            "status": result.status,
            "duration_seconds": result.duration_seconds,
            "operations": _redact_error_payload(result.operations),
            "errors": _redact_error_payload(result.errors),
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat(),
        }
    finally:
        redis_client.close()


@router.post(
    "/trigger/{source_name}",
    responses={404: {"description": "Unknown pipeline source"}},
)
def trigger_single_source(
    source_name: Annotated[
        str,
        Path(
            min_length=1,
            max_length=64,
            pattern=r"^[a-zA-Z0-9 _-]+$",
            description="Human-readable pipeline source label",
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
):
    normalized = " ".join(source_name.strip().lower().split())
    scope = PIPELINE_TRIGGER_ALIASES.get(normalized)

    redis_client = _get_redis()
    try:
        orchestrator = DataPipelineOrchestrator(db, redis_client)
        if scope == "market":
            orchestrator.run_market_pipeline()
            return {
                "status": "ok",
                "scope": "market",
                "message": "Market pipeline executed. See logs for diagnostics.",
            }
        if scope == "intelligence":
            orchestrator.run_intelligence_pipeline()
            return {
                "status": "ok",
                "scope": "intelligence",
                "message": "Intelligence pipeline executed. See logs for diagnostics.",
            }
    finally:
        redis_client.close()

    raise HTTPException(status_code=404, detail="Unknown pipeline source")
