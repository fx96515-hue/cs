"""Compatibility wrapper for LLM provider selection.

Canonical implementation lives in app.domains.assistant.providers.llm.
"""

from app.domains.assistant.providers.llm import (
    BaseLLMProvider,
    DeterministicFallbackProvider,
    GroqProvider,
    OllamaProvider,
    OpenAIProvider,
    get_llm_provider,
    resolve_rag_model,
)
from app.domains.assistant.providers.llm import settings

__all__ = [
    "BaseLLMProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "GroqProvider",
    "DeterministicFallbackProvider",
    "get_llm_provider",
    "resolve_rag_model",
    "settings",
]
