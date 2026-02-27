"""Unit tests for RAG AI Analyst service."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.services.rag_analyst import RAGAnalystService
from app.schemas.rag_analyst import ConversationMessage, RAGResponse

# Test constants
MOCK_COOPERATIVE_SIMILARITY = 0.85
MOCK_ROASTER_SIMILARITY = 0.80


@pytest.fixture
def mock_settings():
    """Mock settings with multi-provider config."""
    with patch("app.services.rag_analyst.settings") as mock:
        mock.RAG_PROVIDER = "ollama"
        mock.RAG_LLM_MODEL = "llama3.1:8b"
        mock.RAG_TEMPERATURE = 0.3
        mock.RAG_MAX_CONTEXT_ENTITIES = 10
        mock.RAG_MAX_CONVERSATION_HISTORY = 20
        mock.RAG_EMBEDDING_PROVIDER = "openai"
        mock.RAG_EMBEDDING_MODEL = "text-embedding-3-small"
        mock.OLLAMA_BASE_URL = "http://localhost:11434"
        mock.OPENAI_API_KEY = "test-key"
        mock.EMBEDDING_MODEL = "text-embedding-3-small"
        yield mock


@pytest.fixture
def mock_settings_no_key():
    """Mock settings without provider availability."""
    with patch("app.services.rag_analyst.settings") as mock:
        mock.RAG_PROVIDER = "openai"
        mock.RAG_LLM_MODEL = "gpt-4o-mini"
        mock.RAG_TEMPERATURE = 0.3
        mock.RAG_MAX_CONTEXT_ENTITIES = 10
        mock.RAG_MAX_CONVERSATION_HISTORY = 20
        mock.OPENAI_API_KEY = None  # No key
        yield mock


@pytest.fixture
def service(mock_settings):
    """Create RAGAnalystService with mocked settings."""
    with patch("app.services.llm_providers.settings", mock_settings):
        with patch("httpx.get") as mock_get:
            # Mock Ollama availability check
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            return RAGAnalystService()


@pytest.fixture
def service_no_key(mock_settings_no_key):
    """Create RAGAnalystService without API key."""
    with patch("app.services.llm_providers.settings", mock_settings_no_key):
        return RAGAnalystService()


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock()
    # Mock cooperative results
    coop_rows = [
        (
            "cooperative",
            1,
            "Test Coop",
            "Cajamarca",
            "Organic, Fair Trade",
            1500,
            "Arabica",
            MOCK_COOPERATIVE_SIMILARITY,
        )
    ]
    # Mock roaster results
    roaster_rows = [
        (
            "roaster",
            2,
            "Test Roaster",
            "Hamburg",
            True,
            True,
            "premium",
            MOCK_ROASTER_SIMILARITY,
        )
    ]

    # Mock execute to return different results based on query
    def mock_execute(query, params):
        result = MagicMock()
        if "cooperatives" in str(query):
            result.fetchall.return_value = coop_rows
        else:
            result.fetchall.return_value = roaster_rows
        return result

    db.execute = mock_execute
    return db


class TestRAGAnalystService:
    """Test RAGAnalystService functionality."""

    def test_is_available_with_key(self, service):
        """Test service is available when API key is configured."""
        assert service.is_available() is True

    def test_is_available_without_key(self, service_no_key):
        """Test service is not available when API key is missing."""
        assert service_no_key.is_available() is False

    def test_initialization(self, service, mock_settings):
        """Test service initializes with correct settings."""
        assert service.model == "llama3.1:8b"
        assert service.temperature == 0.3
        assert service.max_context_entities == 10
        assert service.max_history == 20
        assert service.llm_provider.provider_name() == "ollama"

    @pytest.mark.asyncio
    async def test_ask_success(self, service, mock_db):
        """Test successful question answering."""
        mock_answer = "Das ist eine Testantwort mit Quellenangaben."

        # Mock embedding service
        with patch.object(
            service.embedding_service, "generate_embedding"
        ) as mock_embed:
            mock_embed.return_value = [0.1] * 1536

            # Mock LLM provider
            with patch.object(service.llm_provider, "chat_completion") as mock_chat:
                mock_chat.return_value = {
                    "content": mock_answer,
                    "tokens_used": 500,
                }

                result = await service.ask(
                    question="Welche Kooperativen in Cajamarca haben Fair Trade?",
                    conversation_history=[],
                    db=mock_db,
                )

                assert isinstance(result, RAGResponse)
                assert result.answer == mock_answer
                assert result.model == "llama3.1:8b"
                assert result.tokens_used == 500
                assert len(result.sources) > 0

    @pytest.mark.asyncio
    async def test_ask_no_api_key(self, service_no_key, mock_db):
        """Test asking question without API key raises exception."""
        with pytest.raises(Exception) as exc_info:
            await service_no_key.ask(
                question="Test question",
                conversation_history=[],
                db=mock_db,
            )
        assert "not available" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_retrieve_context(self, service, mock_db):
        """Test context retrieval from database."""
        with patch.object(
            service.embedding_service, "generate_embedding"
        ) as mock_embed:
            mock_embed.return_value = [0.1] * 1536

            context = await service._retrieve_context("test question", mock_db)

            assert len(context) > 0
            assert context[0]["entity_type"] in ["cooperative", "roaster"]
            assert "entity_id" in context[0]
            assert "name" in context[0]
            assert "similarity_score" in context[0]

    @pytest.mark.asyncio
    async def test_retrieve_context_embedding_fails(self, service, mock_db):
        """Test context retrieval when embedding generation fails."""
        with patch.object(
            service.embedding_service, "generate_embedding"
        ) as mock_embed:
            mock_embed.return_value = None

            context = await service._retrieve_context("test question", mock_db)

            assert context == []

    def test_build_system_prompt_with_context(self, service):
        """Test system prompt building with context."""
        context = [
            {
                "entity_type": "cooperative",
                "entity_id": 1,
                "name": "Test Coop",
                "region": "Cajamarca",
                "certifications": "Organic",
                "varieties": "Arabica",
                "altitude_m": 1500,
                "similarity_score": 0.85,
            }
        ]

        prompt = service._build_system_prompt(context)

        assert "KI-Assistent" in prompt
        assert "Kaffee-Sourcing" in prompt
        assert "Test Coop" in prompt
        assert "Cajamarca" in prompt
        assert "ID: 1" in prompt

    def test_build_system_prompt_empty_context(self, service):
        """Test system prompt building with empty context."""
        prompt = service._build_system_prompt([])

        assert "KI-Assistent" in prompt
        assert "keine spezifischen Daten verfügbar" in prompt

    def test_get_provider_info(self, service):
        """Test get_provider_info returns correct information."""
        info = service.get_provider_info()

        assert info["provider"] == "ollama"
        assert info["model"] == "llama3.1:8b"

    @pytest.mark.asyncio
    async def test_conversation_history_handling(self, service, mock_db):
        """Test conversation history is included in API call."""
        history = [
            ConversationMessage(role="user", content="Erste Frage"),
            ConversationMessage(role="assistant", content="Erste Antwort"),
        ]

        with patch.object(
            service.embedding_service, "generate_embedding"
        ) as mock_embed:
            mock_embed.return_value = [0.1] * 1536

            with patch.object(service.llm_provider, "chat_completion") as mock_chat:
                mock_chat.return_value = {
                    "content": "Antwort",
                    "tokens_used": 100,
                }

                await service.ask(
                    question="Zweite Frage",
                    conversation_history=history,
                    db=mock_db,
                )

                # Verify history was included in API call
                call_args = mock_chat.call_args
                messages = call_args[1]["messages"]
                # Should have: system + 2 history + current question
                assert len(messages) >= 4

    @pytest.mark.asyncio
    async def test_api_error_handling(self, service, mock_db):
        """Test handling of provider API errors."""
        with patch.object(
            service.embedding_service, "generate_embedding"
        ) as mock_embed:
            mock_embed.return_value = [0.1] * 1536

            with patch.object(service.llm_provider, "chat_completion") as mock_chat:
                mock_chat.side_effect = Exception("API Error")

                with pytest.raises(Exception):
                    await service.ask(
                        question="Test question",
                        conversation_history=[],
                        db=mock_db,
                    )


class TestGracefulDegradation:
    """Test graceful degradation when service is unavailable."""

    @pytest.mark.asyncio
    async def test_no_api_key_raises_exception(self, service_no_key, mock_db):
        """Test that missing API key raises clear exception."""
        with pytest.raises(Exception) as exc_info:
            await service_no_key.ask("test", [], mock_db)
        assert "not available" in str(exc_info.value).lower()

    def test_service_unavailable_status(self, service_no_key):
        """Test is_available returns False without key."""
        assert service_no_key.is_available() is False
