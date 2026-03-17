"""RAG-based AI analyst service for coffee sourcing intelligence.

This service uses Retrieval-Augmented Generation (RAG) to answer questions
about cooperatives, roasters, market data, and sourcing using the existing
pgvector semantic search infrastructure.
"""

from __future__ import annotations

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domains.assistant.schemas.analyst import (
    ConversationMessage,
    RAGResponse,
    RAGSource,
)
import app.services.embedding as embedding_service
from app.domains.assistant.providers.llm import (
    BaseLLMProvider,
    get_llm_provider,
    resolve_rag_model,
)

log = structlog.get_logger()


class RAGAnalystService:
    """RAG-based AI analyst for coffee sourcing intelligence."""

    def __init__(self) -> None:
        self.llm_provider: BaseLLMProvider = get_llm_provider()
        self.model = resolve_rag_model(self.llm_provider.provider_name())
        self.temperature = settings.RAG_TEMPERATURE
        self.max_context_entities = settings.RAG_MAX_CONTEXT_ENTITIES
        self.max_history = settings.RAG_MAX_CONVERSATION_HISTORY
        self.embedding_service = embedding_service.EmbeddingService()

    def is_available(self) -> bool:
        """Check if RAG service is available (provider configured and reachable)."""
        return self.llm_provider.is_available()

    def get_provider_info(self) -> dict:
        """Get information about the configured provider.

        Returns:
            Dict with provider name and model
        """
        return {
            "provider": self.llm_provider.provider_name(),
            "model": self.model,
        }

    async def ask(
        self,
        question: str,
        conversation_history: list[ConversationMessage],
        db: Session,
    ) -> RAGResponse:
        """Answer a question using RAG.

        Args:
            question: User's question
            conversation_history: Previous conversation messages
            db: Database session

        Returns:
            RAG response with answer and sources

        Raises:
            Exception: If service unavailable or API call fails
        """
        if not self.is_available():
            provider_name = self.llm_provider.provider_name()
            log.warning(
                "rag_service_unavailable",
                provider=provider_name,
                reason="provider_not_available",
            )
            raise Exception(
                f"RAG service not available: {provider_name} provider is not configured or unreachable"
            )

        # Retrieve relevant context
        context = await self._retrieve_context(question, db)
        log.info(
            "rag_context_retrieved",
            question_length=len(question),
            context_entities=len(context),
        )

        # Build system prompt with context
        system_prompt = self._build_system_prompt(context)

        # Build messages for API
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (limited)
        for msg in conversation_history[-self.max_history :]:
            messages.append({"role": msg.role, "content": msg.content})

        # Add current question
        messages.append({"role": "user", "content": question})

        # Call LLM provider
        try:
            result = await self.llm_provider.chat_completion(
                messages=messages,
                temperature=self.temperature,
                model=self.model,
            )

            answer = result["content"]
            tokens_used = result["tokens_used"]

            log.info(
                "rag_answer_generated",
                provider=self.llm_provider.provider_name(),
                question_length=len(question),
                answer_length=len(answer),
                tokens_used=tokens_used,
            )

            # Build sources from context
            sources = [
                RAGSource(
                    entity_type=ctx["entity_type"],
                    entity_id=ctx["entity_id"],
                    name=ctx["name"],
                    similarity_score=ctx["similarity_score"],
                )
                for ctx in context
            ]

            return RAGResponse(
                answer=answer,
                sources=sources,
                model=self.model,
                tokens_used=tokens_used,
            )

        except Exception as e:
            log.error("rag_answer_generation_failed", error=str(e))
            raise

    def _clamp_similarity(self, score: float) -> float:
        """Clamp similarity score to valid range [0.0, 1.0].

        Args:
            score: Raw similarity score

        Returns:
            Clamped score between 0.0 and 1.0
        """
        return max(0.0, min(1.0, score))

    async def _retrieve_context(self, question: str, db: Session) -> list[dict]:
        """Retrieve relevant context entities using pgvector similarity search.

        Args:
            question: User's question
            db: Database session

        Returns:
            List of context entities with metadata
        """
        # Generate embedding for question
        query_embedding = await self.embedding_service.generate_embedding(question)
        if not query_embedding:
            log.warning("rag_context_retrieval_failed", reason="embedding_failed")
            return []

        # Search cooperatives
        coop_query = text(
            """
            SELECT 
                'cooperative' as entity_type,
                id, 
                name, 
                region, 
                certifications,
                altitude_m,
                varieties,
                1 - ((embedding <=> :query_embedding) / 2) AS similarity
            FROM cooperatives
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :query_embedding
            LIMIT :limit
            """
        )

        coop_rows = db.execute(
            coop_query,
            {
                "query_embedding": query_embedding,
                "limit": self.max_context_entities // 2,
            },
        ).fetchall()

        # Search roasters
        roaster_query = text(
            """
            SELECT 
                'roaster' as entity_type,
                id, 
                name, 
                city,
                peru_focus,
                specialty_focus,
                price_position,
                1 - ((embedding <=> :query_embedding) / 2) AS similarity
            FROM roasters
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :query_embedding
            LIMIT :limit
            """
        )

        roaster_rows = db.execute(
            roaster_query,
            {
                "query_embedding": query_embedding,
                "limit": self.max_context_entities // 2,
            },
        ).fetchall()

        # Combine and format results
        context = []

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

        # Sort by similarity and limit total
        context.sort(key=lambda x: x["similarity_score"], reverse=True)
        return context[: self.max_context_entities]

    def _build_no_context_prompt(self, base_prompt: str) -> str:
        return (
            base_prompt
            + "\nAktuell sind keine spezifischen Daten verfuegbar.\n"
            + "\n"
            + "Zusaetzliche Richtlinien fuer diese Situation:\n"
            + "- Erklaere ausdruecklich, dass du fuer diese Antwort keine konkreten Quellen/Entities zur Verfuegung hast.\n"
            + "- Nenne keine Entity-Namen oder -IDs und erfinde keine Quellen.\n"
            + "- Du darfst nur allgemeines Wissen ueber Kaffee-Sourcing nutzen und musst klar machen, dass es sich um allgemeine Informationen ohne konkrete Quellenangabe handelt.\n"
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

    def _build_system_prompt(self, context: list[dict]) -> str:
        """Build system prompt with retrieved context."""
        base_prompt = """Du bist ein KI-Assistent fuer Kaffee-Sourcing und Spezialitaetenkaffee-Handel.
Du hilfst dabei, Informationen ueber Kooperativen, Roestereien, Marktdaten und Sourcing-Moeglichkeiten zu finden und zu analysieren.

Du sprichst primaer Deutsch, kannst aber auch auf Englisch antworten wenn gewuenscht.

WICHTIGE RICHTLINIEN:
- Beantworte Fragen praezise und auf Basis der bereitgestellten Daten
- Nenne, falls vorhanden, die Quellen (Namen und IDs der Entities) in deiner Antwort
- Wenn Daten fehlen oder unvollstaendig sind, sage das klar
- Erfinde keine spezifischen Details zu Entities und gib nichts als aus den Quelldaten stammend aus, wenn es dort nicht vorkommt
- Sei hilfsbereit und professionell
"""

        if not context:
            return self._build_no_context_prompt(base_prompt)

        sections = [
            base_prompt,
            "\n\n=== VERFUEGBARE DATEN ===\n",
            self._render_coops(context),
            self._render_roasters(context),
            "\n=== ENDE DER DATEN ===\n",
        ]
        return "".join(sections)
