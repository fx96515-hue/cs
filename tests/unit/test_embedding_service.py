"""Unit tests for the embedding service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import app.services.embedding as embedding_service
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster


@pytest.fixture
def mock_settings():
    """Mock settings with API key configured (OpenAI path)."""
    with patch("app.services.embedding.settings") as mock:
        mock.OPENAI_API_KEY = "test-api-key"
        mock.EMBEDDING_MODEL = "text-embedding-3-small"
        mock.EMBEDDING_PROVIDER = "openai"
        mock.SENTENCE_TRANSFORMERS_CACHE = None
        yield mock


@pytest.fixture
def mock_settings_no_key():
    """Mock settings without API key."""
    with patch("app.services.embedding.settings") as mock:
        mock.OPENAI_API_KEY = None
        mock.EMBEDDING_MODEL = "text-embedding-3-small"
        mock.EMBEDDING_PROVIDER = "openai"
        mock.SENTENCE_TRANSFORMERS_CACHE = None
        yield mock


@pytest.fixture
def service(mock_settings):
    """Create EmbeddingService with mocked settings."""
    return embedding_service.EmbeddingService()


@pytest.fixture
def service_no_key(mock_settings_no_key):
    """Create EmbeddingService without API key."""
    return embedding_service.EmbeddingService()


@pytest.fixture
def sample_cooperative():
    """Create a sample cooperative entity."""
    coop = MagicMock(spec=Cooperative)
    coop.id = 1
    coop.name = "Test Cooperative"
    coop.region = "Cajamarca"
    coop.certifications = "Organic, Fair Trade"
    coop.varieties = "Arabica, Typica"
    coop.altitude_m = 1500
    coop.notes = "High quality coffee from Peru"
    return coop


@pytest.fixture
def sample_roaster():
    """Create a sample roaster entity."""
    roaster = MagicMock(spec=Roaster)
    roaster.id = 1
    roaster.name = "Test Roastery"
    roaster.city = "Hamburg"
    roaster.peru_focus = True
    roaster.specialty_focus = True
    roaster.price_position = "premium"
    roaster.notes = "Specialty coffee roaster"
    return roaster


class TestEmbeddingService:
    """Test EmbeddingService functionality."""

    def test_is_available_with_key(self, service):
        """Test service is available when API key is configured."""
        assert service.is_available() is True

    def test_is_available_without_key(self, service_no_key):
        """Test service is not available when API key is missing."""
        assert service_no_key.is_available() is False

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, service):
        """Test successful embedding generation."""
        mock_embedding = [0.1] * 1536  # Mock 1536-dimensional vector

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"data": [{"embedding": mock_embedding}]}
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await service.generate_embedding("test text")
            assert result == mock_embedding
            assert len(result) == 1536

    @pytest.mark.asyncio
    async def test_generate_embedding_no_api_key(self, service_no_key):
        """Test embedding generation returns None without API key."""
        result = await service_no_key.generate_embedding("test text")
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, service):
        """Test embedding generation with empty text."""
        result = await service.generate_embedding("")
        assert result is None

        result = await service.generate_embedding("   ")
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_embedding_api_error(self, service):
        """Test handling of API errors."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status.side_effect = Exception("API Error")

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await service.generate_embedding("test text")
            assert result is None

    def test_generate_entity_text_cooperative(self, service, sample_cooperative):
        """Test entity text generation for cooperative."""
        text = service.generate_entity_text(sample_cooperative)
        assert "Test Cooperative" in text
        assert "Cajamarca" in text
        assert "Organic, Fair Trade" in text
        assert "Arabica, Typica" in text
        assert "1500m" in text
        assert "High quality coffee" in text

    def test_generate_entity_text_roaster(self, service, sample_roaster):
        """Test entity text generation for roaster."""
        text = service.generate_entity_text(sample_roaster)
        assert "Test Roastery" in text
        assert "Hamburg" in text
        assert "Peru specialty coffee" in text
        assert "premium" in text
        assert "Specialty coffee roaster" in text


class TestGracefulDegradation:
    """Test graceful degradation when service is unavailable."""

    @pytest.mark.asyncio
    async def test_no_api_key_returns_none(self, service_no_key):
        """Test that missing API key returns None without raising errors."""
        result = await service_no_key.generate_embedding("test")
        assert result is None

    @pytest.mark.asyncio
    async def test_api_error_returns_none(self, service):
        """Test that API errors return None without crashing."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = (
                Exception("Connection failed")
            )

            result = await service.generate_embedding("test")
            assert result is None
