"""Assistant Chat service with Redis session history and streaming RAG.

Extends the existing RAG Analyst capabilities with:
- Redis-based conversation history (keyed by session ID)
- Server-Sent Events (SSE) streaming response
- News and KB context in addition to cooperatives/roasters
"""

from __future__ import annotations

import json
import uuid
from typing import AsyncIterator

import redis as redis_lib
import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domains.assistant.schemas.analyst import RAGSource
import app.services.embedding as embedding_service
from app.domains.assistant.providers.llm import (
    BaseLLMProvider,
    get_llm_provider,
    resolve_rag_model,
)

log = structlog.get_logger()

_REDIS_SESSION_PREFIX = "assistant:session:"


class AssistantService:
    """Streaming RAG chat service with Redis session history."""

    def __init__(self) -> None:
        self.llm_provider: BaseLLMProvider = get_llm_provider()
        self.model = resolve_rag_model(self.llm_provider.provider_name())
        self.temperature = settings.RAG_TEMPERATURE
        self.max_context_entities = settings.RAG_MAX_CONTEXT_ENTITIES
        self.max_history = settings.RAG_MAX_CONVERSATION_HISTORY
        self.session_ttl = settings.ASSISTANT_SESSION_TTL_SECONDS
        self.embedding_service = embedding_service.EmbeddingService()

    def is_available(self) -> bool:
        """Check if the underlying LLM provider is available."""
        return self.llm_provider.is_available()

    def get_provider_info(self) -> dict:
        """Return provider metadata."""
        return {
            "provider": self.llm_provider.provider_name(),
            "model": self.model,
        }

    # ------------------------------------------------------------------
    # Redis session helpers
    # ------------------------------------------------------------------

    def _redis_client(self) -> redis_lib.Redis:
        return redis_lib.from_url(settings.REDIS_URL, decode_responses=True)

    def _session_key(self, session_id: str) -> str:
        return f"{_REDIS_SESSION_PREFIX}{session_id}"

    def load_history(self, session_id: str) -> list[dict]:
        """Load conversation history from Redis.

        Args:
            session_id: Session identifier

        Returns:
            List of message dicts (role/content)
        """
        try:
            client = self._redis_client()
            raw = client.get(self._session_key(session_id))
            client.close()
            if raw and isinstance(raw, str):
                return json.loads(raw)
        except Exception as e:
            log.warning(
                "assistant_session_load_failed", session_id=session_id, error=str(e)
            )
        return []

    def save_history(self, session_id: str, history: list[dict]) -> None:
        """Persist conversation history to Redis.

        Args:
            session_id: Session identifier
            history: Message list to store
        """
        try:
            client = self._redis_client()
            client.setex(
                self._session_key(session_id),
                self.session_ttl,
                json.dumps(history),
            )
            client.close()
        except Exception as e:
            log.warning(
                "assistant_session_save_failed", session_id=session_id, error=str(e)
            )

    # ------------------------------------------------------------------
    # Context retrieval (cooperatives + roasters + recent news)
    # ------------------------------------------------------------------

    def _clamp_similarity(self, score: float) -> float:
        return max(0.0, min(1.0, score))

    async def _retrieve_context(self, question: str, db: Session) -> list[dict]:
        """Retrieve relevant context using pgvector + recent news.

        Args:
            question: User question text
            db: Database session

        Returns:
            List of context dicts (entity metadata + similarity score)
        """
        query_embedding = await self.embedding_service.generate_embedding(question)
        if not query_embedding:
            log.warning("assistant_context_retrieval_failed", reason="embedding_failed")
            return []

        half = max(1, self.max_context_entities // 2)
        context: list[dict] = []

        # --- Cooperatives ---
        coop_rows = db.execute(
            text(
                """
                SELECT
                    'cooperative' as entity_type,
                    id, name, region, certifications, altitude_m, varieties,
                    1 - ((embedding <=> :emb) / 2) AS similarity
                FROM cooperatives
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> :emb
                LIMIT :lim
                """
            ),
            {"emb": query_embedding, "lim": half},
        ).fetchall()

        for row in coop_rows:
            context.append(
                {
                    "entity_type": row[0],
                    "entity_id": row[1],
                    "name": row[2],
                    "region": row[3],
                    "certifications": row[4],
                    "altitude_m": row[5],
                    "varieties": row[6],
                    "similarity_score": self._clamp_similarity(row[7]),
                }
            )

        # --- Roasters ---
        roaster_rows = db.execute(
            text(
                """
                SELECT
                    'roaster' as entity_type,
                    id, name, city, peru_focus, specialty_focus, price_position,
                    1 - ((embedding <=> :emb) / 2) AS similarity
                FROM roasters
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> :emb
                LIMIT :lim
                """
            ),
            {"emb": query_embedding, "lim": half},
        ).fetchall()

        for row in roaster_rows:
            context.append(
                {
                    "entity_type": row[0],
                    "entity_id": row[1],
                    "name": row[2],
                    "city": row[3],
                    "peru_focus": row[4],
                    "specialty_focus": row[5],
                    "price_position": row[6],
                    "similarity_score": self._clamp_similarity(row[7]),
                }
            )

        # --- Recent News (up to 5, text-based, no embedding required) ---
        try:
            news_rows = db.execute(
                text(
                    """
                    SELECT id, title, snippet, topic, published_at
                    FROM news_items
                    ORDER BY retrieved_at DESC NULLS LAST
                    LIMIT 5
                    """
                )
            ).fetchall()

            for row in news_rows:
                context.append(
                    {
                        "entity_type": "news",
                        "entity_id": row[0],
                        "name": row[1],
                        "snippet": row[2],
                        "topic": row[3],
                        "published_at": str(row[4]) if row[4] else None,
                        "similarity_score": 0.5,  # No vector similarity for news
                    }
                )
        except Exception as e:
            log.warning("assistant_news_retrieval_failed", error=str(e))

        context.sort(key=lambda x: x["similarity_score"], reverse=True)
        return context[: self.max_context_entities]

    # ------------------------------------------------------------------
    # System prompt
    # ------------------------------------------------------------------

    def _base_prompt(self) -> str:
        return (
            "Du bist der CoffeeStudio KI-Assistent - ein Experte fuer Spezialitaetenkaffee-Handel, "
            "Rohkaffee-Sourcing, Kooperativen in Peru und internationale Roestereien.\n\n"
            "RICHTLINIEN:\n"
            "- Antworte praezise und auf Basis der bereitgestellten Daten.\n"
            "- Nenne stets die Quellen (Name + ID) in deiner Antwort, wenn du Entities verwendest.\n"
            "- Wenn Daten fehlen, sage das klar - erfinde keine Details.\n"
            "- Primaersprache: Deutsch (auf Wunsch auch Englisch).\n"
        )

    def _render_coops(self, context: list[dict]) -> str:
        coops = [c for c in context if c["entity_type"] == "cooperative"]
        if not coops:
            return ""

        section = "\n## Kooperativen:\n"
        for coop in coops:
            section += f"\n**{coop['name']}** (ID: {coop['entity_id']})\n"
            if coop.get("region"):
                section += f"- Region: {coop['region']}\n"
            if coop.get("certifications"):
                section += f"- Zertifizierungen: {coop['certifications']}\n"
            if coop.get("varieties"):
                section += f"- Sorten: {coop['varieties']}\n"
            if coop.get("altitude_m"):
                section += f"- Hoehe: {coop['altitude_m']}m\n"
        return section

    def _render_roasters(self, context: list[dict]) -> str:
        roasters = [r for r in context if r["entity_type"] == "roaster"]
        if not roasters:
            return ""

        section = "\n## Roestereien:\n"
        for roaster in roasters:
            section += f"\n**{roaster['name']}** (ID: {roaster['entity_id']})\n"
            if roaster.get("city"):
                section += f"- Stadt: {roaster['city']}\n"
            if roaster.get("peru_focus"):
                section += "- Peru-Fokus: Ja\n"
            if roaster.get("specialty_focus"):
                section += "- Specialty-Fokus: Ja\n"
            if roaster.get("price_position"):
                section += f"- Preispositionierung: {roaster['price_position']}\n"
        return section

    def _render_news(self, context: list[dict]) -> str:
        news_items = [n for n in context if n["entity_type"] == "news"]
        if not news_items:
            return ""

        section = "\n## Aktuelle News:\n"
        for item in news_items:
            section += f"\n- **{item['name']}**"
            if item.get("published_at"):
                section += f" ({item['published_at'][:10]})"
            if item.get("snippet"):
                section += f"\n  {item['snippet']}"
            section += "\n"
        return section

    def _build_system_prompt(self, context: list[dict]) -> str:
        """Build system prompt with CoffeeStudio domain knowledge and retrieved context."""
        prompt = self._base_prompt()
        if not context:
            return (
                prompt
                + "\nAktuell sind keine spezifischen Quelldaten verfuegbar. "
                + "Nutze nur allgemeines Kaffee-Wissen und weise darauf hin.\n"
            )

        parts = [
            prompt,
            "\n\n=== VERFUEGBARE DATEN ===\n",
            self._render_coops(context),
            self._render_roasters(context),
            self._render_news(context),
            "\n=== ENDE DER DATEN ===\n",
        ]
        return "".join(parts)
    # ------------------------------------------------------------------
    # Streaming chat
    # ------------------------------------------------------------------

    async def stream_chat(
        self,
        message: str,
        session_id: str | None,
        db: Session,
    ) -> AsyncIterator[str]:
        """Stream a chat response as SSE events.

        Yields Server-Sent Event lines. Each yielded string is a complete
        ``data: ...\\n\\n`` SSE frame.

        Event types:
        - ``{"type": "session", "session_id": "..."}``          – first frame
        - ``{"type": "chunk", "content": "..."}``                – text tokens
        - ``{"type": "done", "sources": [...], "model": "..."}`` – final frame
        - ``{"type": "error", "message": "..."}``                – on failure

        Args:
            message: User message text
            session_id: Existing session ID or None to create a new one
            db: Database session

        Yields:
            SSE-formatted strings
        """
        if not self.is_available():
            yield _sse({"type": "error", "message": "LLM provider not available"})
            return

        # Resolve / create session
        if not session_id:
            session_id = str(uuid.uuid4())

        yield _sse({"type": "session", "session_id": session_id})

        # Load history from Redis
        history = self.load_history(session_id)

        # Retrieve RAG context
        try:
            context = await self._retrieve_context(message, db)
        except Exception as e:
            log.error("assistant_context_error", error=str(e))
            context = []

        system_prompt = self._build_system_prompt(context)

        # Build messages list
        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        messages.extend(history[-self.max_history :])
        messages.append({"role": "user", "content": message})

        # Stream LLM response
        full_answer = ""
        try:
            async for chunk in self.llm_provider.stream_chat_completion(
                messages=messages,
                temperature=self.temperature,
                model=self.model,
            ):
                full_answer += chunk
                yield _sse({"type": "chunk", "content": chunk})
        except Exception as e:
            log.error("assistant_stream_error", error=str(e))
            yield _sse(
                {"type": "error", "message": "Fehler bei der Antwortgenerierung"}
            )
            return

        # Persist updated history to Redis
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": full_answer})
        self.save_history(session_id, history)

        # Build sources list (exclude news from scored sources)
        sources = [
            RAGSource(
                entity_type=ctx["entity_type"],
                entity_id=ctx["entity_id"],
                name=ctx["name"],
                similarity_score=ctx["similarity_score"],
            )
            for ctx in context
            if ctx["entity_type"] != "news"
        ]

        log.info(
            "assistant_chat_completed",
            session_id=session_id,
            provider=self.llm_provider.provider_name(),
            answer_length=len(full_answer),
            sources_count=len(sources),
        )

        yield _sse(
            {
                "type": "done",
                "sources": [s.model_dump() for s in sources],
                "model": self.model,
                "session_id": session_id,
            }
        )


def _sse(payload: dict) -> str:
    """Format a dict as a Server-Sent Events data frame."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
