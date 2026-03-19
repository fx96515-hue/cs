"""Compatibility wrapper for knowledge-base schemas.

Canonical implementation lives in app.domains.kb.schemas.kb.
"""

from app.domains.kb.schemas.kb import KBSeedResponse, KnowledgeDocOut

__all__ = ["KnowledgeDocOut", "KBSeedResponse"]
