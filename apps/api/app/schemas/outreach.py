"""Compatibility wrapper for outreach schemas.

Canonical implementation lives in app.domains.outreach.schemas.outreach.
"""

from app.domains.outreach.schemas.outreach import OutreachRequest, OutreachResponse

__all__ = ["OutreachRequest", "OutreachResponse"]
