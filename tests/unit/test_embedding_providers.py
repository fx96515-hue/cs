"""Unit tests for embedding providers."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import app.services.embedding_providers as embedding_providers


class TestOllamaEmbeddingProvider:
    """Test embedding_providers.OllamaEmbeddingProvider functionality."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for Ollama embeddings."""
        with patch("app.services.embedding_providers.settings") as mock:
            mock.OLLAMA_BASE_URL = "http://localhost:11434"
            mock.RAG_EMBEDDING_MODEL = "nomic-embed-text"
            yield mock

    @pytest.fixture
    def provider(self, mock_settings):
        """Create embedding_providers.OllamaEmbeddingProvider with mocked settings."""
        return embedding_providers.OllamaEmbeddingProvider()

    def test_provider_name(self, provider):
        """Test provider_name returns 'ollama'."""
        assert provider.provider_name() == "ollama"

    def test_embedding_dimensions(self, provider):
        """Test embedding_dimensions returns 768."""
        assert provider.embedding_dimensions() == 768

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, provider):
        """Test successful embedding generation."""
        mock_embedding = [0.1] * 768

        mock_response_data = {"embeddings": [mock_embedding]}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await provider.generate_embedding("Test text")

            assert result == mock_embedding
            assert len(result) == 768

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, provider):
        """Test embedding generation with empty text."""
        result = await provider.generate_embedding("")
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_embedding_whitespace_only(self, provider):
        """Test embedding generation with whitespace-only text."""
        result = await provider.generate_embedding("   ")
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_embedding_connection_error(self, provider):
        """Test embedding generation when Ollama is not reachable."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("Connection refused")
            )

            result = await provider.generate_embedding("Test text")
            assert result is None

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_response(self, provider):
        """Test embedding generation with empty embeddings array."""
        mock_response_data = {"embeddings": []}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await provider.generate_embedding("Test text")
            assert result is None


class TestOpenAIEmbeddingProvider:
    """Test embedding_providers.OpenAIEmbeddingProvider functionality."""

    @pytest.fixture
    def mock_settings_with_key(self):
        """Mock settings with API key."""
        with patch("app.services.embedding_providers.settings") as mock:
            mock.OPENAI_API_KEY = "sk-test-key"
            mock.RAG_EMBEDDING_MODEL = "text-embedding-3-small"
            yield mock

    @pytest.fixture
    def mock_settings_no_key(self):
        """Mock settings without API key."""
        with patch("app.services.embedding_providers.settings") as mock:
            mock.OPENAI_API_KEY = None
            mock.RAG_EMBEDDING_MODEL = "text-embedding-3-small"
            yield mock

    @pytest.fixture
    def provider(self, mock_settings_with_key):
        """Create embedding_providers.OpenAIEmbeddingProvider with API key."""
        return embedding_providers.OpenAIEmbeddingProvider()

    @pytest.fixture
    def provider_no_key(self, mock_settings_no_key):
        """Create embedding_providers.OpenAIEmbeddingProvider without API key."""
        return embedding_providers.OpenAIEmbeddingProvider()

    def test_provider_name(self, provider):
        """Test provider_name returns 'openai'."""
        assert provider.provider_name() == "openai"

    def test_embedding_dimensions(self, provider):
        """Test embedding_dimensions returns 1536."""
        assert provider.embedding_dimensions() == 1536

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, provider):
        """Test successful embedding generation."""
        mock_embedding = [0.1] * 1536

        mock_response_data = {"data": [{"embedding": mock_embedding}]}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await provider.generate_embedding("Test text")

            assert result == mock_embedding
            assert len(result) == 1536

    @pytest.mark.asyncio
    async def test_generate_embedding_no_api_key(self, provider_no_key):
        """Test embedding generation without API key."""
        result = await provider_no_key.generate_embedding("Test text")
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, provider):
        """Test embedding generation with empty text."""
        result = await provider.generate_embedding("")
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_embedding_api_error(self, provider):
        """Test embedding generation with API error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status.side_effect = Exception("API Error")

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await provider.generate_embedding("Test text")
            assert result is None


class TestGetEmbeddingProvider:
    """Test embedding_providers.get_embedding_provider factory function."""

    def test_get_ollama_provider(self):
        """Test factory returns embedding_providers.OllamaEmbeddingProvider."""
        with patch("app.services.embedding_providers.settings") as mock:
            mock.RAG_EMBEDDING_PROVIDER = "ollama"
            mock.OLLAMA_BASE_URL = "http://localhost:11434"
            mock.RAG_EMBEDDING_MODEL = "nomic-embed-text"

            provider = embedding_providers.get_embedding_provider()
            assert isinstance(provider, embedding_providers.OllamaEmbeddingProvider)

    def test_get_openai_provider(self):
        """Test factory returns embedding_providers.OpenAIEmbeddingProvider."""
        with patch("app.services.embedding_providers.settings") as mock:
            mock.RAG_EMBEDDING_PROVIDER = "openai"
            mock.OPENAI_API_KEY = "test-key"
            mock.RAG_EMBEDDING_MODEL = "text-embedding-3-small"

            provider = embedding_providers.get_embedding_provider()
            assert isinstance(provider, embedding_providers.OpenAIEmbeddingProvider)

    def test_get_unknown_provider(self):
        """Test factory raises ValueError for unknown provider."""
        with patch("app.services.embedding_providers.settings") as mock:
            mock.RAG_EMBEDDING_PROVIDER = "unknown"

            with pytest.raises(ValueError) as exc_info:
                embedding_providers.get_embedding_provider()

            assert "Unknown embedding provider" in str(exc_info.value)

    def test_case_insensitive(self):
        """Test factory is case-insensitive."""
        with patch("app.services.embedding_providers.settings") as mock:
            mock.RAG_EMBEDDING_PROVIDER = "OLLAMA"
            mock.OLLAMA_BASE_URL = "http://localhost:11434"
            mock.RAG_EMBEDDING_MODEL = "nomic-embed-text"

            provider = embedding_providers.get_embedding_provider()
            assert isinstance(provider, embedding_providers.OllamaEmbeddingProvider)

    def test_get_local_provider(self):
        """Test factory returns embedding_providers.LocalEmbeddingProvider."""
        with patch("app.services.embedding_providers.settings") as mock:
            mock.RAG_EMBEDDING_PROVIDER = "local"
            mock.EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
            mock.SENTENCE_TRANSFORMERS_CACHE = None

            provider = embedding_providers.get_embedding_provider()
            assert isinstance(provider, embedding_providers.LocalEmbeddingProvider)


class TestLocalEmbeddingProvider:
    """Tests for embedding_providers.LocalEmbeddingProvider (sentence-transformers, CPU-only).

    All tests mock the SentenceTransformer class so no model download is
    required in CI.
    """

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the module-level singleton before each test."""
        original = embedding_providers._local_st_model
        embedding_providers._local_st_model = None
        yield
        embedding_providers._local_st_model = original

    @pytest.fixture
    def mock_st_settings(self):
        """Mock provider settings."""
        with patch("app.services.embedding_providers.settings") as mock:
            mock.EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
            mock.SENTENCE_TRANSFORMERS_CACHE = None
            yield mock

    @pytest.fixture
    def mock_model(self):
        """Return a mock SentenceTransformer that produces 384-dim vectors."""
        import numpy as np

        model = MagicMock()
        model.encode.return_value = np.array([0.1] * 384)
        return model

    @pytest.fixture
    def provider(self, mock_st_settings, mock_model):
        """embedding_providers.LocalEmbeddingProvider with a pre-loaded mock model singleton.

        Sets the module-level singleton directly so no sentence_transformers
        import is triggered during the test.
        """
        embedding_providers._local_st_model = mock_model
        yield embedding_providers.LocalEmbeddingProvider(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    def test_provider_name(self, provider):
        """Test provider_name returns 'local'."""
        assert provider.provider_name() == "local"

    def test_embedding_dimensions(self, provider):
        """Test embedding_dimensions returns 384."""
        assert provider.embedding_dimensions() == 384

    def test_encode_returns_384_floats(self, provider):
        """encode() must return a list of 384 floats."""
        result = provider.encode("specialty coffee from Peru")
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 384
        assert all(isinstance(v, float) for v in result)

    def test_encode_empty_text_returns_none(self, provider):
        """encode() returns None for empty string."""
        assert provider.encode("") is None

    def test_encode_whitespace_only_returns_none(self, provider):
        """encode() returns None for whitespace-only string."""
        assert provider.encode("   ") is None

    def test_encode_none_returns_none(self, provider):
        """encode() returns None when passed None."""
        # encode signature is str but guard against None at runtime
        assert provider.encode(None) is None  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_generate_embedding_async(self, provider):
        """generate_embedding() is an async wrapper around encode()."""
        result = await provider.generate_embedding("test text")
        assert result is not None
        assert len(result) == 384

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_async(self, provider):
        """generate_embedding() returns None for empty text."""
        result = await provider.generate_embedding("")
        assert result is None

    def test_is_importable_when_installed(self):
        """is_importable() returns True when sentence_transformers is present."""
        with patch.dict("sys.modules", {"sentence_transformers": MagicMock()}):
            assert embedding_providers.LocalEmbeddingProvider.is_importable() is True

    def test_is_importable_when_missing(self):
        """is_importable() returns False when sentence_transformers is absent."""
        with patch.dict("sys.modules", {"sentence_transformers": None}):
            assert embedding_providers.LocalEmbeddingProvider.is_importable() is False

    def test_encode_model_error_returns_none(self, mock_model):
        """encode() returns None and does not raise on model error."""
        mock_model.encode.side_effect = RuntimeError("OOM")
        embedding_providers._local_st_model = mock_model

        with patch("app.services.embedding_providers.settings") as mock_settings:
            mock_settings.EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
            mock_settings.SENTENCE_TRANSFORMERS_CACHE = None
            provider = embedding_providers.LocalEmbeddingProvider(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )

        result = provider.encode("some text")
        assert result is None
