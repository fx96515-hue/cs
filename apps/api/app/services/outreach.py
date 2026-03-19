"""Compatibility wrapper for outreach service.

Canonical implementation lives in app.domains.outreach.services.generator.
"""

from app.domains.outreach.services.generator import (
    Language,
    PerplexityClient,
    Purpose,
    _template,
    generate_outreach,
    settings,
)

__all__ = [
    "Language",
    "Purpose",
    "_template",
    "generate_outreach",
    "settings",
    "PerplexityClient",
]
