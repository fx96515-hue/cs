"""Unit tests for LLM providers."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.llm_providers import (
    OllamaProvider,
    OpenAIProvider,
    GroqProvider,
    get_llm_provider,
)


class TestOllamaProvider:
    """Test OllamaProvider functionality."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for Ollama."""
        with patch("app.services.llm_providers.settings") as mock:
            mock.OLLAMA_BASE_URL = "http://localhost:11434"
            yield mock

    @pytest.fixture
    def provider(self, mock_settings):
        """Create OllamaProvider with mocked settings."""
        return OllamaProvider()

    def test_provider_name(self, provider):
        """Test provider_name returns 'ollama'."""
        assert provider.provider_name() == "ollama"

    @patch("httpx.get")
    def test_is_available_success(self, mock_get, provider):
        """Test is_available when Ollama is reachable."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        assert provider.is_available() is True
        mock_get.assert_called_once_with("http://localhost:11434/api/tags", timeout=5.0)

    @patch("httpx.get")
    def test_is_available_connection_error(self, mock_get, provider):
        """Test is_available when Ollama is not reachable."""
        mock_get.side_effect = Exception("Connection refused")

        assert provider.is_available() is False

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, provider):
        """Test successful chat completion."""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]

        mock_response_data = {
            "message": {"content": "Hi there!"},
            "eval_count": 50,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await provider.chat_completion(
                messages=messages, temperature=0.7, model="llama3.1:8b"
            )

            assert result["content"] == "Hi there!"
            assert result["tokens_used"] == 50

    @pytest.mark.asyncio
    async def test_chat_completion_connection_error(self, provider):
        """Test chat completion when Ollama is not reachable."""
        messages = [{"role": "user", "content": "Hello"}]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("Connection refused")
            )

            with pytest.raises(Exception) as exc_info:
                await provider.chat_completion(
                    messages=messages, temperature=0.7, model="llama3.1:8b"
                )

            assert "ollama serve" in str(exc_info.value).lower()


class TestOpenAIProvider:
    """Test OpenAIProvider functionality."""

    @pytest.fixture
    def mock_settings_with_key(self):
        """Mock settings with API key."""
        with patch("app.services.llm_providers.settings") as mock:
            mock.OPENAI_API_KEY = "sk-test-key"
            yield mock

    @pytest.fixture
    def mock_settings_no_key(self):
        """Mock settings without API key."""
        with patch("app.services.llm_providers.settings") as mock:
            mock.OPENAI_API_KEY = None
            yield mock

    @pytest.fixture
    def provider(self, mock_settings_with_key):
        """Create OpenAIProvider with API key."""
        return OpenAIProvider()

    @pytest.fixture
    def provider_no_key(self, mock_settings_no_key):
        """Create OpenAIProvider without API key."""
        return OpenAIProvider()

    def test_provider_name(self, provider):
        """Test provider_name returns 'openai'."""
        assert provider.provider_name() == "openai"

    def test_is_available_with_key(self, provider):
        """Test is_available when API key is configured."""
        assert provider.is_available() is True

    def test_is_available_without_key(self, provider_no_key):
        """Test is_available when API key is missing."""
        assert provider_no_key.is_available() is False

    def test_is_available_empty_key(self):
        """Test is_available with empty API key."""
        with patch("app.services.llm_providers.settings") as mock:
            mock.OPENAI_API_KEY = "   "
            provider = OpenAIProvider()
            assert provider.is_available() is False

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, provider):
        """Test successful chat completion."""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]

        mock_response_data = {
            "choices": [{"message": {"content": "Hello! How can I help?"}}],
            "usage": {"total_tokens": 75},
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await provider.chat_completion(
                messages=messages, temperature=0.3, model="gpt-4o-mini"
            )

            assert result["content"] == "Hello! How can I help?"
            assert result["tokens_used"] == 75

    @pytest.mark.asyncio
    async def test_chat_completion_no_api_key(self, provider_no_key):
        """Test chat completion without API key."""
        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(Exception) as exc_info:
            await provider_no_key.chat_completion(
                messages=messages, temperature=0.3, model="gpt-4o-mini"
            )

        assert "not configured" in str(exc_info.value).lower()


class TestGroqProvider:
    """Test GroqProvider functionality."""

    @pytest.fixture
    def mock_settings_with_key(self):
        """Mock settings with API key."""
        with patch("app.services.llm_providers.settings") as mock:
            mock.GROQ_API_KEY = "gsk-test-key"
            yield mock

    @pytest.fixture
    def mock_settings_no_key(self):
        """Mock settings without API key."""
        with patch("app.services.llm_providers.settings") as mock:
            mock.GROQ_API_KEY = None
            yield mock

    @pytest.fixture
    def provider(self, mock_settings_with_key):
        """Create GroqProvider with API key."""
        return GroqProvider()

    @pytest.fixture
    def provider_no_key(self, mock_settings_no_key):
        """Create GroqProvider without API key."""
        return GroqProvider()

    def test_provider_name(self, provider):
        """Test provider_name returns 'groq'."""
        assert provider.provider_name() == "groq"

    def test_is_available_with_key(self, provider):
        """Test is_available when API key is configured."""
        assert provider.is_available() is True

    def test_is_available_without_key(self, provider_no_key):
        """Test is_available when API key is missing."""
        assert provider_no_key.is_available() is False

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, provider):
        """Test successful chat completion."""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]

        mock_response_data = {
            "choices": [{"message": {"content": "Hi! I'm here to help."}}],
            "usage": {"total_tokens": 60},
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await provider.chat_completion(
                messages=messages, temperature=0.3, model="llama-3.1-8b-instant"
            )

            assert result["content"] == "Hi! I'm here to help."
            assert result["tokens_used"] == 60


class TestGetLLMProvider:
    """Test get_llm_provider factory function."""

    def test_get_ollama_provider(self):
        """Test factory returns OllamaProvider."""
        with patch("app.services.llm_providers.settings") as mock:
            mock.RAG_PROVIDER = "ollama"
            mock.OLLAMA_BASE_URL = "http://localhost:11434"

            provider = get_llm_provider()
            assert isinstance(provider, OllamaProvider)

    def test_get_openai_provider(self):
        """Test factory returns OpenAIProvider."""
        with patch("app.services.llm_providers.settings") as mock:
            mock.RAG_PROVIDER = "openai"
            mock.OPENAI_API_KEY = "test-key"

            provider = get_llm_provider()
            assert isinstance(provider, OpenAIProvider)

    def test_get_groq_provider(self):
        """Test factory returns GroqProvider."""
        with patch("app.services.llm_providers.settings") as mock:
            mock.RAG_PROVIDER = "groq"
            mock.GROQ_API_KEY = "test-key"

            provider = get_llm_provider()
            assert isinstance(provider, GroqProvider)

    def test_get_unknown_provider(self):
        """Test factory raises ValueError for unknown provider."""
        with patch("app.services.llm_providers.settings") as mock:
            mock.RAG_PROVIDER = "unknown"

            with pytest.raises(ValueError) as exc_info:
                get_llm_provider()

            assert "Unknown RAG provider" in str(exc_info.value)

    def test_case_insensitive(self):
        """Test factory is case-insensitive."""
        with patch("app.services.llm_providers.settings") as mock:
            mock.RAG_PROVIDER = "OLLAMA"
            mock.OLLAMA_BASE_URL = "http://localhost:11434"

            provider = get_llm_provider()
            assert isinstance(provider, OllamaProvider)
