"""Tests for LLM provider selection and fallback behavior."""

import asyncio

from app.services.llm_providers import (
    DeterministicFallbackProvider,
    get_llm_provider,
    resolve_rag_model,
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


def test_get_llm_provider_auto_prefers_openrouter(monkeypatch):
    monkeypatch.setattr("app.services.llm_providers.settings.RAG_PROVIDER", "auto")
    monkeypatch.setattr(
        "app.services.llm_providers.OpenRouterProvider.is_available",
        lambda self: True,
    )
    monkeypatch.setattr(
        "app.services.llm_providers.GroqProvider.is_available",
        lambda self: True,
    )
    monkeypatch.setattr(
        "app.services.llm_providers.OllamaProvider.is_available",
        lambda self: True,
    )

    provider = get_llm_provider()
    assert provider.provider_name() == "openrouter"


def test_get_llm_provider_auto_falls_back_to_groq_when_openrouter_unavailable(monkeypatch):
    monkeypatch.setattr("app.services.llm_providers.settings.RAG_PROVIDER", "auto")
    monkeypatch.setattr(
        "app.services.llm_providers.OpenRouterProvider.is_available",
        lambda self: False,
    )
    monkeypatch.setattr(
        "app.services.llm_providers.GroqProvider.is_available",
        lambda self: True,
    )
    monkeypatch.setattr(
        "app.services.llm_providers.OllamaProvider.is_available",
        lambda self: True,
    )

    provider = get_llm_provider()
    assert provider.provider_name() == "groq"


def test_resolve_rag_model_uses_provider_default_when_no_override(monkeypatch):
    monkeypatch.setattr("app.services.llm_providers.settings.RAG_LLM_MODEL", "")
    monkeypatch.setattr(
        "app.services.llm_providers.settings.RAG_LLM_MODEL_GROQ",
        "llama-3.1-8b-instant",
    )

    assert resolve_rag_model("groq") == "llama-3.1-8b-instant"


def test_resolve_rag_model_uses_openrouter_default(monkeypatch):
    monkeypatch.setattr("app.services.llm_providers.settings.RAG_LLM_MODEL", "")
    monkeypatch.setattr(
        "app.services.llm_providers.settings.RAG_LLM_MODEL_OPENROUTER",
        "meta-llama/llama-3.3-8b-instruct:free",
    )

    assert (
        resolve_rag_model("openrouter")
        == "meta-llama/llama-3.3-8b-instruct:free"
    )
