"""Compatibility wrapper for dedup service.

Canonical implementation lives in app.domains.dedup.services.merge.
"""

from app.domains.dedup.services.merge import (
    DedupPair,
    _domain,
    _score,
    get_merge_history,
    merge_entities,
    suggest_duplicates,
)

__all__ = [
    "DedupPair",
    "_domain",
    "_score",
    "suggest_duplicates",
    "merge_entities",
    "get_merge_history",
]
