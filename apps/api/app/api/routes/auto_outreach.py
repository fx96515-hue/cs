"""Auto-outreach API routes."""

from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role, get_db
from app.schemas.auto_outreach import (
    CreateCampaignIn,
    CampaignOut,
    OutreachSuggestionOut,
    EntityOutreachStatusOut,
)
from app.services import auto_outreach


router = APIRouter()


@router.post("/campaign", response_model=CampaignOut)
def create_campaign(
    payload: CreateCampaignIn,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    """Create and launch an outreach campaign."""
    try:
        result = auto_outreach.create_campaign(
            db,
            name=payload.name,
            entity_type=payload.entity_type,
            language=payload.language,
            purpose=payload.purpose,
            min_quality_score=payload.min_quality_score,
            min_reliability_score=payload.min_reliability_score,
            min_economics_score=payload.min_economics_score,
            region=payload.region,
            certification=payload.certification,
            limit=payload.limit,
            refine_with_llm=payload.refine_with_llm,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import structlog

        structlog.get_logger().error("create_campaign_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Campaign creation failed")


@router.get("/suggestions", response_model=list[OutreachSuggestionOut])
def get_suggestions(
    entity_type: Literal["cooperative", "roaster"],
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    """Get AI-suggested outreach targets."""
    try:
        suggestions = auto_outreach.get_outreach_suggestions(
            db, entity_type=entity_type, limit=limit
        )
        return suggestions
    except Exception as e:
        import structlog

        structlog.get_logger().error("get_suggestions_failed", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to get outreach suggestions"
        )


@router.get("/status/{entity_type}/{entity_id}", response_model=EntityOutreachStatusOut)
def get_entity_status(
    entity_type: Literal["cooperative", "roaster"],
    entity_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    """Get outreach status for a specific entity."""
    try:
        status = auto_outreach.get_entity_outreach_status(
            db, entity_type=entity_type, entity_id=entity_id
        )
        return status
    except Exception as e:
        import structlog

        structlog.get_logger().error("get_entity_status_failed", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to get entity outreach status"
        )
