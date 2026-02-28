import os
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


broker_url = os.getenv("CELERY_BROKER_URL", settings.REDIS_URL)
result_backend = os.getenv("CELERY_RESULT_BACKEND", settings.REDIS_URL)
task_always_eager = _env_flag("CELERY_TASK_ALWAYS_EAGER", False)
task_eager_propagates = _env_flag("CELERY_TASK_EAGER_PROPAGATES", True)
task_ignore_result = _env_flag("CELERY_TASK_IGNORE_RESULT", False)

celery = Celery(
    "coffeestudio",
    broker=broker_url,
    backend=result_backend,
)

celery.conf.update(
    timezone=settings.TZ,
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60 * 10,
    broker_connection_retry_on_startup=True,
    task_always_eager=task_always_eager,
    task_eager_propagates=task_eager_propagates,
    task_ignore_result=task_ignore_result,
)


def _build_schedule() -> dict:
    """Build Celery beat schedule from ENV-driven refresh times."""
    sched: dict = {}
    for idx, (hh, mm) in enumerate(
        settings.refresh_times_list(settings.MARKET_REFRESH_TIMES), start=1
    ):
        sched[f"market_refresh_{idx:02d}"] = {
            "task": "app.workers.tasks.refresh_market",
            "schedule": crontab(minute=mm, hour=hh),
        }
    for idx, (hh, mm) in enumerate(
        settings.refresh_times_list(settings.NEWS_REFRESH_TIMES), start=1
    ):
        sched[f"news_refresh_{idx:02d}"] = {
            "task": "app.workers.tasks.refresh_news",
            "schedule": crontab(minute=mm, hour=hh),
        }

    # Intelligence refresh (every 6 hours by default)
    intelligence_times = getattr(
        settings, "INTELLIGENCE_REFRESH_TIMES", "06:00,12:00,18:00,00:00"
    )
    for idx, (hh, mm) in enumerate(
        settings.refresh_times_list(intelligence_times), start=1
    ):
        sched[f"intelligence_refresh_{idx:02d}"] = {
            "task": "app.workers.tasks.refresh_intelligence",
            "schedule": crontab(minute=mm, hour=hh),
        }

    # Auto-enrich stale entities (daily at 03:00 by default)
    auto_enrich_time = getattr(settings, "AUTO_ENRICH_TIME", "03:00")
    if auto_enrich_time:
        parts = auto_enrich_time.split(":")
        hh_str, mm_str = parts[0], parts[1]
        sched["auto_enrich_stale"] = {
            "task": "app.workers.tasks.auto_enrich_stale",
            "schedule": crontab(minute=int(mm_str), hour=int(hh_str)),
        }

    # Daily embedding backfill (04:00 by default; configurable via EMBEDDINGS_TIME)
    embeddings_time = getattr(settings, "EMBEDDINGS_TIME", "04:00")
    if embeddings_time:
        try:
            parts = embeddings_time.split(":")
            hh_str, mm_str = parts[0], parts[1]
            sched["generate_embeddings"] = {
                "task": "app.workers.tasks.generate_embeddings",
                "schedule": crontab(minute=int(mm_str), hour=int(hh_str)),
                "kwargs": {"entity_type": None, "batch_size": 100},
            }
        except (IndexError, ValueError) as exc:
            import logging

            logging.getLogger(__name__).warning(
                "Invalid EMBEDDINGS_TIME format %r (expected HH:MM) – "
                "daily embedding backfill schedule skipped. Error: %s",
                embeddings_time,
                exc,
            )

    # Daily anomaly scan (02:00 by default; configurable via ANOMALY_SCAN_TIME)
    anomaly_scan_time = getattr(settings, "ANOMALY_SCAN_TIME", "02:00")
    if anomaly_scan_time and getattr(settings, "ANOMALY_DETECTION_ENABLED", True):
        try:
            parts = anomaly_scan_time.split(":")
            hh_str, mm_str = parts[0], parts[1]
            sched["run_anomaly_scan"] = {
                "task": "app.workers.tasks.run_anomaly_scan",
                "schedule": crontab(minute=int(mm_str), hour=int(hh_str)),
            }
        except (IndexError, ValueError) as exc:
            import logging

            logging.getLogger(__name__).warning(
                "Invalid ANOMALY_SCAN_TIME format %r (expected HH:MM) – "
                "daily anomaly scan schedule skipped. Error: %s",
                anomaly_scan_time,
                exc,
            )

    return sched


celery.conf.beat_schedule = _build_schedule()

# Ensure task modules are discovered without creating an import cycle.
celery.autodiscover_tasks(["app.workers"])
