"""Compatibility wrapper for auto-outreach service.

Canonical implementation lives in app.domains.auto_outreach.services.campaigns.
"""

from app.domains.auto_outreach.services.campaigns import (
    OutreachStatus,
    create_campaign,
    generate_outreach,
    get_entity_outreach_status,
    get_outreach_suggestions,
    select_top_candidates,
)

__all__ = [
    "OutreachStatus",
    "select_top_candidates",
    "create_campaign",
    "get_outreach_suggestions",
    "get_entity_outreach_status",
    "generate_outreach",
]