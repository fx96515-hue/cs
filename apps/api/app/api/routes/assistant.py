"""Compatibility wrapper for assistant chat routes.

Canonical implementation lives in app.domains.assistant.api.chat_routes.
"""

from app.domains.assistant.api.chat_routes import router

__all__ = ["router"]
