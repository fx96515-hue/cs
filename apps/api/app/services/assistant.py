"""Compatibility wrapper for assistant service.

Canonical implementation lives in app.domains.assistant.services.chat_service.
"""

from app.domains.assistant.services.chat_service import AssistantService

__all__ = ["AssistantService"]
