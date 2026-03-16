"""Compatibility wrapper for assistant schemas.

Canonical implementation lives in app.domains.assistant.schemas.chat.
"""

from app.domains.assistant.schemas.chat import AssistantStatusResponse, ChatRequest

__all__ = ["ChatRequest", "AssistantStatusResponse"]
