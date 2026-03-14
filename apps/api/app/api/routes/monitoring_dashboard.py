from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.services.data_pipeline.freshness import DataFreshnessMonitor
from app.services.data_pipeline.phase2_orchestrator import Phase2DataPipelineFacade
from app.services.orchestration.phase4_scheduler import (
    AlertingSystem,
    CollectionScheduler,
    PipelineMonitor,
)

router = APIRouter()

DbDep = Annotated[Session, Depends(get_db)]
ViewerDep = Annotated[None, Depends(require_role("admin", "analyst", "viewer"))]


@router.get("/dashboard")
def monitoring_dashboard(
    db: DbDep,
    _: ViewerDep,
):
    freshness = DataFreshnessMonitor(db).get_freshness_report()
    scheduler_jobs = CollectionScheduler.jobs()
    alert_summary = AlertingSystem.summary(db)
    phase4_health = PipelineMonitor.get_pipeline_health(db)

    return {
        "pipeline_health": freshness,
        "schedule_status": {
            "total_jobs": len(scheduler_jobs),
            "next_jobs": scheduler_jobs[:5],
        },
        "active_alerts": alert_summary.get("unacknowledged", 0),
        "total_alerts": sum(
            int(alert_summary.get(key, 0))
            for key in ("total", "critical", "high", "medium", "low", "unacknowledged")
        ),
        "provider_summary": Phase2DataPipelineFacade.provider_summary(),
        "phase4_health": phase4_health,
    }


@router.get("/health")
def monitoring_health(
    db: DbDep,
    _: ViewerDep,
):
    return PipelineMonitor.get_pipeline_health(db)


@router.get("/sources")
def monitoring_sources(
    db: DbDep,
    _: ViewerDep,
):
    freshness = DataFreshnessMonitor(db).get_freshness_report()
    categories = freshness.get("categories", {})
    rows: list[dict] = []
    for category_name, items in categories.items():
        for item_name, payload in items.items():
            rows.append(
                {
                    "name": f"{category_name}:{item_name}",
                    "status": payload.get("status", "unknown"),
                    "last_updated": payload.get("last_updated"),
                    "age_hours": payload.get("age_hours"),
                    "reason": payload.get("reason"),
                }
            )
    return {
        "total_sources": len(rows),
        "healthy": sum(1 for row in rows if row["status"] == "fresh"),
        "sources": rows,
        "provider_catalog": Phase2DataPipelineFacade.provider_catalog(),
    }


@router.get("/schedules")
def monitoring_schedules(
    _: ViewerDep,
):
    jobs = CollectionScheduler.jobs()
    return {
        "total": len(jobs),
        "schedules": jobs,
        "summary": CollectionScheduler.summary(),
    }


@router.get("/alerts")
def monitoring_alerts(
    db: DbDep,
    _: ViewerDep,
):
    return AlertingSystem.summary(db)
