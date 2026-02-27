"""Schemas for auto-outreach API."""

from typing import Literal
from pydantic import BaseModel


class CreateCampaignIn(BaseModel):
    """Request to create an outreach campaign."""

    name: str
    entity_type: Literal["cooperative", "roaster"]
    language: Literal["de", "en", "es"] = "de"
    purpose: Literal["sourcing_pitch", "sample_request"] = "sourcing_pitch"
    min_quality_score: float | None = None
    min_reliability_score: float | None = None
    min_economics_score: float | None = None
    region: str | None = None
    certification: str | None = None
    limit: int = 50
    refine_with_llm: bool = True


class CampaignTargetOut(BaseModel):
    """Campaign target output."""

    entity_id: int
    name: str
    status: str
    message: str | None = None
    used_llm: bool | None = None
    error: str | None = None


class CampaignOut(BaseModel):
    """Campaign output."""

    status: str
    campaign_name: str
    entity_type: str
    targets_count: int
    targets: list[CampaignTargetOut]


class OutreachSuggestionOut(BaseModel):
    """Outreach suggestion output."""

    entity_type: str
    entity_id: int
    name: str
    region: str | None
    quality_score: float | None
    reliability_score: float | None
    economics_score: float | None
    total_score: float | None
    certifications: str | None
    website: str | None
    contact_email: str | None
    reason: str
    last_contact: str | None


class EntityOutreachStatusOut(BaseModel):
    """Entity outreach status output."""

    entity_type: str
    entity_id: int
    status: str
    last_contact: str | None = None
    events: list[dict]
