"""Tests for LLM provider selection and fallback behavior."""

import asyncio

from app.services.llm_providers import (
    DeterministicFallbackProvider,
    get_llm_provider,
)


def test_get_llm_provider_falls_back_when_unavailable(monkeypatch):
    """When configured provider is unavailable, fallback provider should be used."""
    monkeypatch.setattr("app.services.llm_providers.settings.RAG_PROVIDER", "ollama")
    monkeypatch.setattr(
        "app.services.llm_providers.OllamaProvider.is_available",
        lambda self: False,
    )

    provider = get_llm_provider()
    assert isinstance(provider, DeterministicFallbackProvider)


def test_deterministic_fallback_provider_returns_content():
    provider = DeterministicFallbackProvider()
    out = asyncio.run(
        provider.chat_completion(
            messages=[{"role": "user", "content": "Welche Koops sind relevant?"}],
            temperature=0.0,
            model="ignored",
        )
    )
    assert isinstance(out["content"], str)
    assert "deterministische" in out["content"].lower()
