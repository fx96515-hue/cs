"""Compatibility wrapper for dedup schemas.

Canonical implementation lives in app.domains.dedup.schemas.dedup.
"""

from app.domains.dedup.schemas.dedup import (
    DedupPairOut,
    MergeEntitiesIn,
    MergeHistoryOut,
    MergeResultOut,
)

__all__ = [
    "DedupPairOut",
    "MergeEntitiesIn",
    "MergeResultOut",
    "MergeHistoryOut",
]