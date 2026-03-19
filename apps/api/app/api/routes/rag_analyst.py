"""Compatibility wrapper for RAG analyst routes.

Canonical implementation lives in app.domains.assistant.api.analyst_routes.
"""

from app.domains.assistant.api.analyst_routes import router

__all__ = ["router"]
