"""Operations dashboard API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role, get_db
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster
from app.services.data_pipeline.freshness import DataFreshnessMonitor
from app.models.data_quality_flag import DataQualityFlag
from app.domains.quality_alerts.services.alerts import get_alert_summary


router = APIRouter()
DbSessionDep = Annotated[Session, Depends(get_db)]
AnalystPermissionDep = Annotated[object, Depends(require_role("admin", "analyst"))]


@router.get("/overview")
def get_overview(
    db: DbSessionDep,
    _: AnalystPermissionDep,
):
    """Get system health overview."""
    # Entity counts
    total_coops = db.query(Cooperative).filter(Cooperative.deleted_at.is_(None)).count()
    active_coops = (
        db.query(Cooperative)
        .filter(Cooperative.status == "active", Cooperative.deleted_at.is_(None))
        .count()
    )
    total_roasters = db.query(Roaster).filter(Roaster.deleted_at.is_(None)).count()
    active_roasters = (
        db.query(Roaster)
        .filter(Roaster.status == "active", Roaster.deleted_at.is_(None))
        .count()
    )

    # Data freshness
    monitor = DataFreshnessMonitor(db)
    stale_coops = monitor.get_stale_entities("cooperative", stale_days=30)
    stale_roasters = monitor.get_stale_entities("roaster", stale_days=30)

    # Alerts
    alert_summary = get_alert_summary(db)

    return {
        "entities": {
            "cooperatives": {
                "total": total_coops,
                "active": active_coops,
                "stale": len(stale_coops),
            },
            "roasters": {
                "total": total_roasters,
                "active": active_roasters,
                "stale": len(stale_roasters),
            },
        },
        "alerts": alert_summary,
        "data_quality": {
            "freshness_status": "good"
            if len(stale_coops) < 10 and len(stale_roasters) < 10
            else "needs_attention",
            "open_flags": db.query(DataQualityFlag)
            .filter(DataQualityFlag.resolved_at.is_(None))
            .count(),
            "critical_flags": db.query(DataQualityFlag)
            .filter(
                DataQualityFlag.resolved_at.is_(None),
                DataQualityFlag.severity == "critical",
            )
            .count(),
        },
    }


@router.get("/entity-health")
def get_entity_health(
    db: DbSessionDep,
    _: AnalystPermissionDep,
):
    """Get per-entity health scores with trend data."""
    # Get cooperatives with scores
    coops = (
        db.query(Cooperative)
        .filter(
            Cooperative.quality_score.isnot(None),
            Cooperative.deleted_at.is_(None),
        )
        .order_by(Cooperative.total_score.desc())
        .limit(50)
        .all()
    )

    # Get roasters with scores
    roasters = (
        db.query(Roaster)
        .filter(Roaster.total_score.isnot(None), Roaster.deleted_at.is_(None))
        .order_by(Roaster.total_score.desc())
        .limit(50)
        .all()
    )

    return {
        "cooperatives": [
            {
                "id": c.id,
                "name": c.name,
                "quality_score": c.quality_score,
                "reliability_score": c.reliability_score,
                "economics_score": c.economics_score,
                "total_score": c.total_score,
                "last_scored_at": c.last_scored_at.isoformat()
                if c.last_scored_at
                else None,
            }
            for c in coops
        ],
        "roasters": [
            {
                "id": r.id,
                "name": r.name,
                "total_score": r.total_score,
                "last_scored_at": r.last_scored_at.isoformat()
                if r.last_scored_at
                else None,
            }
            for r in roasters
        ],
    }


@router.get("/pipeline-status")
def get_pipeline_status(
    db: DbSessionDep,
    _: AnalystPermissionDep,
):
    """Get data pipeline status."""
    # This is a simplified implementation
    # In production, would check Redis for circuit breaker states
    monitor = DataFreshnessMonitor(db)

    return {
        "status": "operational",
        "freshness": {
            "cooperative_stale_count": len(
                monitor.get_stale_entities("cooperative", stale_days=30)
            ),
            "roaster_stale_count": len(
                monitor.get_stale_entities("roaster", stale_days=30)
            ),
        },
        "circuit_breakers": {
            "market_data": "closed",
            "intelligence": "closed",
            "enrichment": "closed",
        },
    }
