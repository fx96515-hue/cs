"""Compatibility wrapper for source schemas.

Canonical implementation lives in app.domains.sources.schemas.source.
"""

from app.domains.sources.schemas.source import (
    ALLOWED_SOURCE_KINDS,
    SourceCreate,
    SourceOut,
    SourceUpdate,
)

__all__ = ["ALLOWED_SOURCE_KINDS", "SourceCreate", "SourceUpdate", "SourceOut"]
