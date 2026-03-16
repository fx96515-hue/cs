"""PR721 Phase-4 compatibility facade for scheduling and monitoring."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.data_quality_flag import DataQualityFlag
from app.services.data_pipeline.freshness import DataFreshnessMonitor
from app.services.data_pipeline.phase2_orchestrator import Phase2DataPipelineFacade
from app.domains.quality_alerts.services.alerts import get_alert_summary
from app.workers.celery_app import celery


def _format_cron_field(values: set[int] | set[str]) -> str:
    if not values:
        return "*"
    return ",".join(sorted(str(value) for value in values))


class CollectionScheduler:
    @staticmethod
    def jobs() -> list[dict[str, Any]]:
        schedule = celery.conf.beat_schedule or {}
        jobs: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        for job_id, entry in schedule.items():
            cron = entry["schedule"]
            jobs.append(
                {
                    "id": job_id,
                    "task": entry["task"],
                    "schedule": (
                        f"{_format_cron_field(getattr(cron, 'minute', set()))} "
                        f"{_format_cron_field(getattr(cron, 'hour', set()))} * * *"
                    ),
                    "nextRunAt": (now + cron.remaining_estimate(now)).isoformat(),
                    "kwargs": entry.get("kwargs") or {},
                }
            )
        return jobs

    @classmethod
    def summary(cls) -> dict[str, Any]:
        jobs = cls.jobs()
        return {
            "total_jobs": len(jobs),
            "active_tasks": len(jobs),
            "execution_history": 0,
            "failed_tasks": 0,
        }


class PipelineMonitor:
    @staticmethod
    def get_pipeline_health(db: Session) -> dict[str, Any]:
        freshness = DataFreshnessMonitor(db).get_freshness_report()
        alerts = get_alert_summary(db)
        open_flags = (
            db.query(DataQualityFlag)
            .filter(DataQualityFlag.resolved_at.is_(None))
            .count()
        )
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": freshness.get("overall_status"),
            "freshness": freshness,
            "open_flags": open_flags,
            "alert_summary": alerts,
            "provider_summary": Phase2DataPipelineFacade.provider_summary(),
        }


class AlertingSystem:
    @staticmethod
    def summary(db: Session) -> dict[str, Any]:
        return get_alert_summary(db)
