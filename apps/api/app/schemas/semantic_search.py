"""Compatibility wrapper for semantic-search schemas.

Canonical implementation lives in app.domains.semantic_search.schemas.semantic_search.
"""

from app.domains.semantic_search.schemas.semantic_search import (
    SemanticSearchResponse,
    SemanticSearchResult,
    SimilarEntityResponse,
    SimilarEntityResult,
)

__all__ = [
    "SemanticSearchResult",
    "SemanticSearchResponse",
    "SimilarEntityResult",
    "SimilarEntityResponse",
]
