"""Embedding service for semantic search.

Supports a local/free pipeline (sentence-transformers, default) and the
legacy OpenAI path. The active provider is selected via the
``EMBEDDING_PROVIDER`` setting (default: ``"local"``).
"""

from __future__ import annotations

import inspect
import structlog
from typing import Union

import httpx

from app.core.config import settings
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster

log = structlog.get_logger()


class EmbeddingService:
    """Service for generating entity embeddings.

    When ``EMBEDDING_PROVIDER`` is ``"local"`` (the default), embeddings are
    produced by the :class:`~app.services.embedding_providers.LocalEmbeddingProvider`
    using the sentence-transformers CPU model (384 dimensions, no API key needed).

    When ``EMBEDDING_PROVIDER`` is ``"openai"``, the legacy OpenAI API path is
    used (requires ``OPENAI_API_KEY``).

    Features:
    - Generates embeddings from text
    - Graceful degradation when provider is unavailable
    - Batch processing support
    - Entity-specific text preprocessing
    """

    def __init__(self) -> None:
        self.provider_name = getattr(settings, "EMBEDDING_PROVIDER", "openai")
        self.model = settings.EMBEDDING_MODEL
        # OpenAI-specific (kept for backward compatibility)
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1/embeddings"
        self.timeout = 30.0

    # ------------------------------------------------------------------
    # Availability
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Return True if the configured provider can generate embeddings."""
        if self.provider_name == "local":
            from app.services.embedding_providers import LocalEmbeddingProvider

            return LocalEmbeddingProvider.is_importable()
        # OpenAI path
        return self.api_key is not None and len(self.api_key.strip()) > 0

    # ------------------------------------------------------------------
    # Core generation helpers
    # ------------------------------------------------------------------

    def _local_provider(self):
        from app.services.embedding_providers import LocalEmbeddingProvider

        return LocalEmbeddingProvider(
            model_name=self.model,
            cache_folder=getattr(settings, "SENTENCE_TRANSFORMERS_CACHE", None),
        )

    async def generate_embedding(self, text: str) -> list[float] | None:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats (384 dims for local, 1536 for OpenAI) or None
        """
        if not self.is_available():
            log.warning("embedding_service_unavailable", provider=self.provider_name)
            return None

        if not text or not text.strip():
            log.warning("embedding_empty_text")
            return None

        if self.provider_name == "local":
            return self._local_provider().encode(text)

        # --- OpenAI path ---
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "input": text,
                    },
                    timeout=self.timeout,
                )
                status_result = response.raise_for_status()
                if inspect.isawaitable(status_result):
                    await status_result
                data = response.json()
                if inspect.isawaitable(data):
                    data = await data
                embedding = data["data"][0]["embedding"]
                log.info(
                    "embedding_generated",
                    text_length=len(text),
                    embedding_dim=len(embedding),
                )
                return embedding
        except httpx.HTTPStatusError as e:
            log.error(
                "openai_api_error",
                status_code=e.response.status_code,
                error=str(e),
            )
            return None
        except Exception as e:
            log.error("embedding_generation_failed", error=str(e))
            return None

    async def generate_embeddings_batch(
        self, texts: list[str]
    ) -> list[list[float] | None]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings (or None for failed/empty items)
        """
        if not self.is_available():
            log.warning("embedding_service_unavailable", provider=self.provider_name)
            return [None] * len(texts)

        if self.provider_name == "local":
            provider = self._local_provider()
            return [provider.encode(t) for t in texts]

        # --- OpenAI batch path ---
        valid_texts = [(i, t) for i, t in enumerate(texts) if t and t.strip()]
        if not valid_texts:
            log.warning("embedding_batch_all_empty")
            return [None] * len(texts)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "input": [t for _, t in valid_texts],
                    },
                    timeout=self.timeout * 2,
                )
                status_result = response.raise_for_status()
                if inspect.isawaitable(status_result):
                    await status_result
                data = response.json()
                if inspect.isawaitable(data):
                    data = await data

                results: list[list[float] | None] = [None] * len(texts)
                for (orig_idx, _), emb_data in zip(valid_texts, data["data"]):
                    results[orig_idx] = emb_data["embedding"]

                log.info(
                    "embeddings_batch_generated",
                    total=len(texts),
                    successful=sum(1 for r in results if r is not None),
                )
                return results
        except Exception as e:
            log.error("batch_embedding_failed", error=str(e))
            return [None] * len(texts)

    # ------------------------------------------------------------------
    # Entity text preprocessing
    # ------------------------------------------------------------------

    def generate_entity_text(self, entity: Union[Cooperative, Roaster]) -> str:
        """Build a deterministic text representation of an entity for embedding.

        Combines relevant fields with ``" | "`` as separator.

        Args:
            entity: Cooperative or Roaster instance

        Returns:
            Combined text representation
        """
        parts = []

        parts.append(f"Name: {entity.name}")

        if isinstance(entity, Cooperative):
            if entity.region:
                parts.append(f"Region: {entity.region}")
            if entity.certifications:
                parts.append(f"Certifications: {entity.certifications}")
            if entity.varieties:
                parts.append(f"Varieties: {entity.varieties}")
            if entity.altitude_m:
                parts.append(f"Altitude: {entity.altitude_m}m")
            if entity.notes:
                parts.append(f"Notes: {entity.notes[:500]}")
        elif isinstance(entity, Roaster):
            if entity.city:
                parts.append(f"City: {entity.city}")
            if entity.peru_focus:
                parts.append("Focus: Peru specialty coffee")
            if entity.specialty_focus:
                parts.append("Focus: Specialty coffee")
            if entity.price_position:
                parts.append(f"Price position: {entity.price_position}")
            if entity.notes:
                parts.append(f"Notes: {entity.notes[:500]}")

        return " | ".join(parts)

    async def generate_entity_embedding(
        self, entity: Union[Cooperative, Roaster]
    ) -> list[float] | None:
        """Generate embedding for an entity.

        Args:
            entity: Cooperative or Roaster instance

        Returns:
            Embedding vector or None if generation failed
        """
        text = self.generate_entity_text(entity)
        return await self.generate_embedding(text)
