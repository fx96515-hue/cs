"""Unit tests for AssistantService (streaming RAG chat with Redis session history)."""

from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch

from app.services.assistant import AssistantService, _sse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MOCK_EMBEDDING = [0.1] * 384


def make_settings(**overrides):
    """Return a mock settings object."""
    m = MagicMock()
    m.RAG_PROVIDER = "ollama"
    m.RAG_LLM_MODEL = "llama3.1:8b"
    m.RAG_TEMPERATURE = 0.3
    m.RAG_MAX_CONTEXT_ENTITIES = 10
    m.RAG_MAX_CONVERSATION_HISTORY = 20
    m.RAG_EMBEDDING_PROVIDER = "local"
    m.RAG_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    m.OLLAMA_BASE_URL = "http://localhost:11434"
    m.OPENAI_API_KEY = None
    m.GROQ_API_KEY = None
    m.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    m.REDIS_URL = "redis://localhost:6379"
    m.ASSISTANT_SESSION_TTL_SECONDS = 86400
    m.ASSISTANT_ENABLED = True
    for k, v in overrides.items():
        setattr(m, k, v)
    return m


@pytest.fixture
def mock_settings():
    s = make_settings()
    with (
        patch("app.services.assistant.settings", s),
        patch("app.services.llm_providers.settings", s),
        patch("httpx.get") as mock_get,
    ):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp
        yield s


@pytest.fixture
def service(mock_settings):
    return AssistantService()


@pytest.fixture
def mock_db():
    db = MagicMock()

    coop_rows = [
        ("cooperative", 1, "Test Coop", "Cajamarca", "Organic", 1500, "Arabica", 0.85)
    ]
    roaster_rows = [
        ("roaster", 2, "Test Roaster", "Hamburg", True, True, "premium", 0.80)
    ]
    news_rows = [(10, "Coffee Market Update", "Prices rose 5%", "market", None)]

    def mock_execute(query, params=None):
        result = MagicMock()
        q = str(query)
        if "cooperatives" in q:
            result.fetchall.return_value = coop_rows
        elif "roasters" in q:
            result.fetchall.return_value = roaster_rows
        elif "news_items" in q:
            result.fetchall.return_value = news_rows
        else:
            result.fetchall.return_value = []
        return result

    db.execute = mock_execute
    return db


# ---------------------------------------------------------------------------
# SSE helper
# ---------------------------------------------------------------------------


class TestSseHelper:
    def test_sse_format(self):
        frame = _sse({"type": "chunk", "content": "hello"})
        assert frame.startswith("data: ")
        assert frame.endswith("\n\n")
        payload = json.loads(frame[6:])
        assert payload["type"] == "chunk"
        assert payload["content"] == "hello"


# ---------------------------------------------------------------------------
# Service availability
# ---------------------------------------------------------------------------


class TestAssistantServiceAvailability:
    def test_is_available_ollama_up(self, service):
        assert service.is_available() is True

    def test_is_available_ollama_down(self, mock_settings):
        with patch("httpx.get", side_effect=Exception("connection refused")):
            svc = AssistantService()
            assert svc.is_available() is False

    def test_get_provider_info(self, service):
        info = service.get_provider_info()
        assert info["provider"] == "ollama"
        assert info["model"] == "llama3.1:8b"


# ---------------------------------------------------------------------------
# Redis session history
# ---------------------------------------------------------------------------


class TestSessionHistory:
    def test_save_and_load_history(self, service):
        history = [{"role": "user", "content": "Hello"}]
        fake_redis = MagicMock()

        with patch.object(service, "_redis_client", return_value=fake_redis):
            service.save_history("sess-1", history)
            fake_redis.setex.assert_called_once()
            # Key should contain the session id
            call_args = fake_redis.setex.call_args[0]
            assert "sess-1" in call_args[0]

    def test_load_history_returns_parsed_json(self, service):
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hey"},
        ]
        fake_redis = MagicMock()
        fake_redis.get.return_value = json.dumps(history)

        with patch.object(service, "_redis_client", return_value=fake_redis):
            loaded = service.load_history("sess-1")

        assert loaded == history

    def test_load_history_missing_key_returns_empty(self, service):
        fake_redis = MagicMock()
        fake_redis.get.return_value = None

        with patch.object(service, "_redis_client", return_value=fake_redis):
            loaded = service.load_history("sess-nonexistent")

        assert loaded == []

    def test_load_history_redis_error_returns_empty(self, service):
        with patch.object(
            service, "_redis_client", side_effect=Exception("redis down")
        ):
            loaded = service.load_history("sess-1")
        assert loaded == []

    def test_save_history_redis_error_does_not_raise(self, service):
        with patch.object(
            service, "_redis_client", side_effect=Exception("redis down")
        ):
            # Should not raise
            service.save_history("sess-1", [{"role": "user", "content": "x"}])


# ---------------------------------------------------------------------------
# Context retrieval
# ---------------------------------------------------------------------------


class TestContextRetrieval:
    @pytest.mark.asyncio
    async def test_retrieve_context_returns_entities(self, service, mock_db):
        with patch.object(
            service.embedding_service, "generate_embedding", return_value=MOCK_EMBEDDING
        ):
            ctx = await service._retrieve_context("test question", mock_db)

        assert len(ctx) > 0
        types = {c["entity_type"] for c in ctx}
        assert "cooperative" in types or "roaster" in types

    @pytest.mark.asyncio
    async def test_retrieve_context_embedding_failure(self, service, mock_db):
        with patch.object(
            service.embedding_service, "generate_embedding", return_value=None
        ):
            ctx = await service._retrieve_context("test", mock_db)
        assert ctx == []

    @pytest.mark.asyncio
    async def test_retrieve_context_includes_news(self, service, mock_db):
        with patch.object(
            service.embedding_service, "generate_embedding", return_value=MOCK_EMBEDDING
        ):
            ctx = await service._retrieve_context("market update", mock_db)
        news = [c for c in ctx if c["entity_type"] == "news"]
        assert len(news) > 0


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------


class TestBuildSystemPrompt:
    def test_prompt_with_cooperative(self, service):
        ctx = [
            {
                "entity_type": "cooperative",
                "entity_id": 1,
                "name": "CENFROCAFE",
                "region": "Cajamarca",
                "certifications": "Fair Trade",
                "varieties": "Typica",
                "altitude_m": 1800,
                "similarity_score": 0.9,
            }
        ]
        prompt = service._build_system_prompt(ctx)
        assert "CENFROCAFE" in prompt
        assert "Cajamarca" in prompt
        assert "ID: 1" in prompt

    def test_prompt_with_news(self, service):
        ctx = [
            {
                "entity_type": "news",
                "entity_id": 5,
                "name": "Coffee Prices Surge",
                "snippet": "Global coffee prices rose sharply.",
                "topic": "market",
                "published_at": "2026-02-01",
                "similarity_score": 0.5,
            }
        ]
        prompt = service._build_system_prompt(ctx)
        assert "Coffee Prices Surge" in prompt

    def test_prompt_empty_context(self, service):
        prompt = service._build_system_prompt([])
        assert "keine spezifischen Quelldaten" in prompt


# ---------------------------------------------------------------------------
# stream_chat
# ---------------------------------------------------------------------------


class TestStreamChat:
    @pytest.mark.asyncio
    async def test_stream_chat_yields_session_and_chunks(self, service, mock_db):
        async def fake_stream(*args, **kwargs):
            yield "Hallo "
            yield "Welt!"

        with (
            patch.object(
                service.embedding_service,
                "generate_embedding",
                return_value=MOCK_EMBEDDING,
            ),
            patch.object(
                service.llm_provider, "stream_chat_completion", side_effect=fake_stream
            ),
            patch.object(service, "load_history", return_value=[]),
            patch.object(service, "save_history"),
        ):
            events = []
            async for frame in service.stream_chat("Hallo", None, mock_db):
                events.append(json.loads(frame[6:]))

        types = [e["type"] for e in events]
        assert "session" in types
        assert "chunk" in types
        assert "done" in types

        chunks = [e["content"] for e in events if e["type"] == "chunk"]
        assert "".join(chunks) == "Hallo Welt!"

    @pytest.mark.asyncio
    async def test_stream_chat_reuses_session_id(self, service, mock_db):
        async def fake_stream(*args, **kwargs):
            yield "ok"

        with (
            patch.object(
                service.embedding_service,
                "generate_embedding",
                return_value=MOCK_EMBEDDING,
            ),
            patch.object(
                service.llm_provider, "stream_chat_completion", side_effect=fake_stream
            ),
            patch.object(service, "load_history", return_value=[]),
            patch.object(service, "save_history"),
        ):
            events = []
            async for frame in service.stream_chat(
                "Hi", "existing-session-123", mock_db
            ):
                events.append(json.loads(frame[6:]))

        session_event = next(e for e in events if e["type"] == "session")
        assert session_event["session_id"] == "existing-session-123"

    @pytest.mark.asyncio
    async def test_stream_chat_provider_unavailable(self, service, mock_db):
        with patch.object(service, "is_available", return_value=False):
            events = []
            async for frame in service.stream_chat("Hello", None, mock_db):
                events.append(json.loads(frame[6:]))

        assert any(e["type"] == "error" for e in events)

    @pytest.mark.asyncio
    async def test_stream_chat_llm_error_yields_error_event(self, service, mock_db):
        async def failing_stream(*args, **kwargs):
            raise Exception("LLM exploded")
            yield  # make it a generator

        with (
            patch.object(
                service.embedding_service,
                "generate_embedding",
                return_value=MOCK_EMBEDDING,
            ),
            patch.object(
                service.llm_provider,
                "stream_chat_completion",
                side_effect=failing_stream,
            ),
            patch.object(service, "load_history", return_value=[]),
        ):
            events = []
            async for frame in service.stream_chat("Test", None, mock_db):
                events.append(json.loads(frame[6:]))

        assert any(e["type"] == "error" for e in events)
