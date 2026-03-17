from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.deps import require_role
from app.workers.celery_app import celery

router = APIRouter()

ViewerPermissionDep = Annotated[
    object, Depends(require_role("admin", "analyst", "viewer"))
]
AnalystPermissionDep = Annotated[object, Depends(require_role("admin", "analyst"))]

JOB_METADATA: dict[str, dict[str, str]] = {
    "market_refresh": {
        "description": "Aktualisiert Marktbeobachtungen und erzeugt Tagesreports.",
        "category": "pipeline",
    },
    "news_refresh": {
        "description": "Aktualisiert News und stoest nachgelagerte Auswertungen an.",
        "category": "pipeline",
    },
    "intelligence_refresh": {
        "description": "Laedt Intelligence- und Wettersignale fuer Peru nach.",
        "category": "pipeline",
    },
    "auto_enrich_stale": {
        "description": "Reichert veraltete Kooperativen und Roestereien automatisiert an.",
        "category": "maintenance",
    },
    "generate_embeddings": {
        "description": "Erzeugt Embeddings fuer Suche und Kontextaufbereitung.",
        "category": "ml",
    },
    "run_anomaly_scan": {
        "description": "Fuehrt die taegliche Anomaliepruefung ueber Scores und Marktwerte aus.",
        "category": "maintenance",
    },
}


def _format_cron_field(values: set[int] | set[str]) -> str:
    if not values:
        return "*"
    rendered = sorted(str(value) for value in values)
    return ",".join(rendered)


def _humanize_cron(minute: str, hour: str) -> str:
    if minute == "*" and hour == "*":
        return "Fortlaufend"
    if "," in hour:
        hours = ", ".join(f"{int(value):02d}:{int(minute):02d}" for value in hour.split(","))
        return f"Mehrfach taeglich: {hours}"
    if minute == "0" and hour != "*":
        return f"Taeglich um {int(hour):02d}:00"
    if hour == "*" and minute != "*":
        return f"Stuendlich um Minute {minute}"
    return f"Cron {minute} {hour} * * *"


def _schedule_payload(job_id: str, entry: dict[str, Any]) -> dict[str, Any]:
    schedule = entry["schedule"]
    minute = _format_cron_field(getattr(schedule, "minute", set()))
    hour = _format_cron_field(getattr(schedule, "hour", set()))
    metadata_key = job_id
    for prefix in ("_01", "_02", "_03", "_04", "_05"):
        if metadata_key.endswith(prefix):
            metadata_key = metadata_key[: -len(prefix)]
            break
    metadata = JOB_METADATA.get(
        metadata_key,
        {"description": "Konfigurierter Hintergrundjob.", "category": "maintenance"},
    )

    now = datetime.now(timezone.utc)
    remaining = schedule.remaining_estimate(now)
    next_run = (now + remaining).isoformat()

    return {
        "id": job_id,
        "task": entry["task"],
        "description": metadata["description"],
        "category": metadata["category"],
        "schedule": f"{minute} {hour} * * *",
        "scheduleHuman": _humanize_cron(minute, hour),
        "nextRunAt": next_run,
        "enabled": True,
        "kwargs": entry.get("kwargs") or {},
    }


def _get_jobs() -> list[dict[str, Any]]:
    schedule = celery.conf.beat_schedule or {}
    return [_schedule_payload(job_id, entry) for job_id, entry in schedule.items()]


@router.get("/jobs")
def scheduler_jobs(_: ViewerPermissionDep):
    return _get_jobs()


@router.get("/summary")
def scheduler_summary(_: ViewerPermissionDep):
    jobs = _get_jobs()
    categories: dict[str, int] = {}
    for job in jobs:
        categories[job["category"]] = categories.get(job["category"], 0) + 1

    return {
        "total": len(jobs),
        "enabled": len(jobs),
        "categories": categories,
        "celery_eager": bool(getattr(celery.conf, "task_always_eager", False)),
    }


@router.post(
    "/jobs/{job_id}/run",
    responses={404: {"description": "Unknown scheduler job"}},
)
def run_scheduler_job(
    job_id: Annotated[
        str,
        Path(
            min_length=1,
            max_length=64,
            pattern=r"^[a-z0-9_:-]+$",
            description="Scheduler job key from Celery beat schedule",
        ),
    ],
    _: AnalystPermissionDep,
):
    schedule = celery.conf.beat_schedule or {}
    if job_id not in schedule:
        raise HTTPException(status_code=404, detail="Unknown scheduler job")

    entry = schedule[job_id]
    task = celery.send_task(
        entry["task"],
        args=entry.get("args") or [],
        kwargs=entry.get("kwargs") or {},
    )
    return {"status": "queued", "task_id": task.id, "job_id": job_id}


@router.get("/tasks/{task_id}")
def scheduler_task_status(
    task_id: Annotated[
        str,
        Path(
            min_length=1,
            max_length=128,
            pattern=r"^[A-Za-z0-9._:-]+$",
            description="Celery task id",
        ),
    ],
    _: ViewerPermissionDep,
):
    result = AsyncResult(task_id, app=celery)
    payload = None
    try:
        payload = result.result if result.ready() else None
    except Exception:
        payload = None
    return {
        "task_id": task_id,
        "state": result.state,
        "ready": result.ready(),
        "result": payload,
    }
