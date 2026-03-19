"""Compatibility wrapper for auto-outreach schemas.

Canonical implementation lives in app.domains.auto_outreach.schemas.auto_outreach.
"""

from app.domains.auto_outreach.schemas.auto_outreach import (
    CampaignOut,
    CampaignTargetOut,
    CreateCampaignIn,
    EntityOutreachStatusOut,
    OutreachSuggestionOut,
)

__all__ = [
    "CreateCampaignIn",
    "CampaignTargetOut",
    "CampaignOut",
    "OutreachSuggestionOut",
    "EntityOutreachStatusOut",
]
