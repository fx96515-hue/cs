"""Auto-outreach engine for automated outreach campaigns."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, cast
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from app.models.cooperative import Cooperative
from app.models.roaster import Roaster
from app.models.entity_event import EntityEvent
from app.services.outreach import generate_outreach, Language, Purpose


OutreachStatus = Literal["pending", "sent", "responded", "follow_up_needed"]


def select_top_candidates(
    db: Session,
    *,
    entity_type: str,
    min_quality_score: float | None = None,
    min_reliability_score: float | None = None,
    min_economics_score: float | None = None,
    region: str | None = None,
    certification: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Select top cooperative/roaster candidates for outreach.

    Args:
        db: Database session
        entity_type: 'cooperative' or 'roaster'
        min_quality_score: Minimum quality score filter
        min_reliability_score: Minimum reliability score filter
        min_economics_score: Minimum economics score filter
        region: Region filter
        certification: Certification filter (checks if contained in certifications)
        limit: Max candidates to return

    Returns:
        List of candidate dicts with entity info
    """
    if entity_type not in {"cooperative", "roaster"}:
        raise ValueError("entity_type must be cooperative|roaster")

    # Build query - handle different models separately for proper typing
    if entity_type == "cooperative":
        stmt_coop = select(Cooperative).filter(Cooperative.status == "active")

        # Apply filters
        if min_quality_score is not None:
            stmt_coop = stmt_coop.filter(Cooperative.quality_score >= min_quality_score)
        if min_reliability_score is not None:
            stmt_coop = stmt_coop.filter(
                Cooperative.reliability_score >= min_reliability_score
            )
        if min_economics_score is not None:
            stmt_coop = stmt_coop.filter(
                Cooperative.economics_score >= min_economics_score
            )
        if region:
            stmt_coop = stmt_coop.filter(Cooperative.region == region)
        if certification:
            stmt_coop = stmt_coop.filter(
                Cooperative.certifications.ilike(f"%{certification}%")
            )

        # Order by total score descending, handling None values
        stmt_coop = stmt_coop.order_by(
            Cooperative.total_score.desc().nullslast()
        ).limit(limit)

        result = db.execute(stmt_coop)
        entities = result.scalars().all()
    else:
        # Roaster doesn't have region, certifications, or individual score fields
        stmt_roaster = select(Roaster).filter(Roaster.status == "active")

        # Order by total score descending, handling None values
        stmt_roaster = stmt_roaster.order_by(
            Roaster.total_score.desc().nullslast()
        ).limit(limit)

        result = db.execute(stmt_roaster)
        entities = result.scalars().all()

    return [
        {
            "entity_type": entity_type,
            "entity_id": e.id,
            "name": e.name,
            "region": getattr(e, "region", None),
            "quality_score": getattr(e, "quality_score", None),
            "reliability_score": getattr(e, "reliability_score", None),
            "economics_score": getattr(e, "economics_score", None),
            "total_score": getattr(e, "total_score", None),
            "certifications": getattr(e, "certifications", None),
            "website": getattr(e, "website", None),
            "contact_email": getattr(e, "contact_email", None),
        }
        for e in entities
    ]


def create_campaign(
    db: Session,
    *,
    name: str,
    entity_type: str,
    language: Language = "de",
    purpose: Purpose = "sourcing_pitch",
    min_quality_score: float | None = None,
    min_reliability_score: float | None = None,
    min_economics_score: float | None = None,
    region: str | None = None,
    certification: str | None = None,
    limit: int = 50,
    refine_with_llm: bool = True,
) -> dict[str, Any]:
    """Create and launch an outreach campaign.

    Args:
        db: Database session
        name: Campaign name
        entity_type: 'cooperative' or 'roaster'
        language: Outreach language
        purpose: Outreach purpose
        min_quality_score: Min quality score filter
        min_reliability_score: Min reliability score filter
        min_economics_score: Min economics score filter
        region: Region filter
        certification: Certification filter
        limit: Max targets
        refine_with_llm: Use AI enhancement

    Returns:
        Campaign result with targets and generated messages
    """
    # Select candidates
    candidates = select_top_candidates(
        db,
        entity_type=entity_type,
        min_quality_score=min_quality_score,
        min_reliability_score=min_reliability_score,
        min_economics_score=min_economics_score,
        region=region,
        certification=certification,
        limit=limit,
    )

    # Generate outreach for each candidate
    targets = []
    for candidate in candidates:
        try:
            # Generate personalized outreach
            outreach_result = generate_outreach(
                db,
                entity_type=entity_type,
                entity_id=candidate["entity_id"],
                language=language,
                purpose=purpose,
                refine_with_llm=refine_with_llm,
            )

            # Track outreach status
            db.add(
                EntityEvent(
                    entity_type=entity_type,
                    entity_id=candidate["entity_id"],
                    event_type="outreach_campaign_added",
                    payload={
                        "campaign_name": name,
                        "language": language,
                        "purpose": purpose,
                        "status": "pending",
                    },
                )
            )

            targets.append(
                {
                    "entity_id": candidate["entity_id"],
                    "name": candidate["name"],
                    "status": "pending",
                    "message": outreach_result["text"],
                    "used_llm": outreach_result["used_llm"],
                }
            )
        except Exception as e:
            targets.append(
                {
                    "entity_id": candidate["entity_id"],
                    "name": candidate["name"],
                    "status": "error",
                    "error": str(e),
                }
            )

    db.commit()

    return {
        "status": "ok",
        "campaign_name": name,
        "entity_type": entity_type,
        "targets_count": len(targets),
        "targets": targets,
    }


def get_outreach_suggestions(
    db: Session, *, entity_type: str, limit: int = 20
) -> list[dict[str, Any]]:
    """Get AI-suggested outreach targets based on scores.

    Suggests entities with high scores that haven't been contacted recently.

    Args:
        db: Database session
        entity_type: 'cooperative' or 'roaster'
        limit: Max suggestions

    Returns:
        List of suggested targets
    """
    # Get high-scoring candidates
    candidates = select_top_candidates(
        db,
        entity_type=entity_type,
        min_quality_score=70.0,
        min_reliability_score=60.0,
        limit=limit * 2,  # Get more to filter
    )

    # Filter out recently contacted entities
    suggestions = []
    for candidate in candidates:
        # Check if entity was recently contacted
        recent_outreach = (
            db.query(EntityEvent)
            .filter(
                and_(
                    EntityEvent.entity_type == entity_type,
                    EntityEvent.entity_id == candidate["entity_id"],
                    or_(
                        EntityEvent.event_type == "outreach_generated",
                        EntityEvent.event_type == "outreach_campaign_added",
                    ),
                )
            )
            .order_by(EntityEvent.created_at.desc())
            .first()
        )

        # Only suggest if not contacted in last 30 days (simplified check)
        should_suggest = False
        if not recent_outreach:
            should_suggest = True
        else:
            # Handle both timezone-aware and naive datetimes
            # Cast created_at to datetime for type checking
            created_at = cast(datetime, recent_outreach.created_at)
            if created_at.tzinfo is None:
                days_since = (datetime.utcnow() - created_at).days
            else:
                days_since = (datetime.now(timezone.utc) - created_at).days
            should_suggest = days_since > 30

        if should_suggest:
            suggestions.append(
                {
                    **candidate,
                    "reason": "High scores, no recent outreach",
                    "last_contact": (
                        cast(datetime, recent_outreach.created_at).isoformat()
                        if recent_outreach
                        else None
                    ),
                }
            )

        if len(suggestions) >= limit:
            break

    return suggestions


def get_entity_outreach_status(
    db: Session, *, entity_type: str, entity_id: int
) -> dict[str, Any]:
    """Get outreach status for a specific entity.

    Args:
        db: Database session
        entity_type: 'cooperative' or 'roaster'
        entity_id: Entity ID

    Returns:
        Outreach status dict
    """
    # Get all outreach events for entity
    events = (
        db.query(EntityEvent)
        .filter(
            and_(
                EntityEvent.entity_type == entity_type,
                EntityEvent.entity_id == entity_id,
                or_(
                    EntityEvent.event_type == "outreach_generated",
                    EntityEvent.event_type == "outreach_campaign_added",
                    EntityEvent.event_type == "outreach_response",
                ),
            )
        )
        .order_by(EntityEvent.created_at.desc())
        .all()
    )

    if not events:
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "status": "not_contacted",
            "events": [],
        }

    # Determine current status
    latest_event = events[0]
    status = "pending"
    if latest_event.event_type == "outreach_response":
        status = "responded"
    else:
        # Handle both timezone-aware and naive datetimes
        # Cast created_at to datetime for type checking
        created_at = cast(datetime, latest_event.created_at)
        if created_at.tzinfo is None:
            # If created_at is naive, use naive datetime for comparison
            days_since = (datetime.utcnow() - created_at).days
        else:
            # If created_at is aware, use aware datetime for comparison
            days_since = (datetime.now(timezone.utc) - created_at).days

        if days_since > 7:
            status = "follow_up_needed"

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "status": status,
        "last_contact": cast(datetime, latest_event.created_at).isoformat(),
        "events": [
            {
                "event_type": e.event_type,
                "created_at": cast(datetime, e.created_at).isoformat(),
                "payload": e.payload,
            }
            for e in events
        ],
    }
