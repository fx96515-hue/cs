"""Compatibility wrapper for semantic-search routes.

Canonical implementation lives in app.domains.semantic_search.api.routes.
"""

from app.domains.semantic_search.api.routes import (
    EmbeddingService,
    _require_search_enabled,
    _search_cooperatives,
    _search_roasters,
    find_similar_entities,
    router,
    semantic_search,
    settings,
)

__all__ = [
    "router",
    "settings",
    "EmbeddingService",
    "semantic_search",
    "find_similar_entities",
    "_require_search_enabled",
    "_search_cooperatives",
    "_search_roasters",
]
