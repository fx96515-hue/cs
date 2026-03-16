"""Compatibility wrapper for knowledge_graph routes.

Canonical implementation lives in app.domains.knowledge_graph.api.routes.
"""

from app.domains.knowledge_graph.api.routes import *  # noqa: F401,F403
from app.domains.knowledge_graph.api.routes import router

__all__ = ["router"]
