"""Embedding Provider abstraction for multi-provider support.

Supports Local/sentence-transformers (CPU, 384 dim), Ollama (local, 768 dim)
and OpenAI (cloud, 1536 dim) embeddings.
"""

from __future__ import annotations

import inspect
import structlog
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.core.config import settings

log = structlog.get_logger()

# Module-level singleton for the sentence-transformers model so it is loaded
# only once per worker process.  Only one model configuration is supported per
# worker process: whichever model name is first resolved wins.
_local_st_model: Any = None


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def generate_embedding(self, text: str) -> list[float] | None:
        """Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None if generation failed
        """
        raise NotImplementedError

    @abstractmethod
    def embedding_dimensions(self) -> int:
        """Return embedding vector dimensions.

        Returns:
            Number of dimensions in embedding vectors
        """
        raise NotImplementedError

    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name."""
        raise NotImplementedError


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """Ollama embeddings - local, free."""

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.RAG_EMBEDDING_MODEL
        self.timeout = 30.0

    async def generate_embedding(self, text: str) -> list[float] | None:
        """Generate embedding using Ollama.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (768 dimensions) or None if failed
        """
        if not text or not text.strip():
            log.warning("ollama_embedding_empty_text")
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/embed",
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

                # Ollama returns {"embeddings": [[0.1, 0.2, ...]]}
                embeddings = data.get("embeddings", [[]])
                if embeddings and len(embeddings) > 0:
                    embedding = embeddings[0]
                    log.info(
                        "ollama_embedding_generated",
                        text_length=len(text),
                        embedding_dim=len(embedding),
                        model=self.model,
                    )
                    return embedding
                else:
                    log.warning("ollama_embedding_empty_response")
                    return None

        except httpx.HTTPStatusError as e:
            log.error(
                "ollama_embedding_api_error",
                status_code=e.response.status_code,
                error=str(e),
            )
            return None
        except httpx.ConnectError as e:
            log.error("ollama_embedding_connection_error", error=str(e))
            return None
        except Exception as e:
            log.error("ollama_embedding_generation_failed", error=str(e))
            return None

    def embedding_dimensions(self) -> int:
        """Return embedding dimensions for nomic-embed-text.

        Returns:
            768 dimensions
        """
        return 768

    def provider_name(self) -> str:
        """Return provider name."""
        return "ollama"


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embeddings - existing implementation."""

    def __init__(self) -> None:
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.RAG_EMBEDDING_MODEL
        self.base_url = "https://api.openai.com/v1/embeddings"
        self.timeout = 30.0

    async def generate_embedding(self, text: str) -> list[float] | None:
        """Generate embedding using OpenAI.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (1536 dimensions) or None if failed
        """
        if not self.api_key or not self.api_key.strip():
            log.warning("openai_embedding_no_api_key")
            return None

        if not text or not text.strip():
            log.warning("openai_embedding_empty_text")
            return None

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
                    "openai_embedding_generated",
                    text_length=len(text),
                    embedding_dim=len(embedding),
                    model=self.model,
                )
                return embedding

        except httpx.HTTPStatusError as e:
            log.error(
                "openai_embedding_api_error",
                status_code=e.response.status_code,
                error=str(e),
            )
            return None
        except Exception as e:
            log.error("openai_embedding_generation_failed", error=str(e))
            return None

    def embedding_dimensions(self) -> int:
        """Return embedding dimensions for text-embedding-3-small.

        Returns:
            1536 dimensions
        """
        return 1536

    def provider_name(self) -> str:
        """Return provider name."""
        return "openai"


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """Local CPU-only embeddings via sentence-transformers.

    Uses ``sentence-transformers/all-MiniLM-L6-v2`` (384 dims) by default.
    The underlying SentenceTransformer model is loaded lazily and cached as a
    module-level singleton so it is initialised only once per worker process.
    """

    def __init__(
        self,
        model_name: str | None = None,
        cache_folder: str | None = None,
    ) -> None:
        self._model_name = model_name or settings.EMBEDDING_MODEL
        self._cache_folder = cache_folder or settings.SENTENCE_TRANSFORMERS_CACHE

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @staticmethod
    def is_importable() -> bool:
        """Return True if sentence-transformers is installed."""
        try:
            import sentence_transformers  # noqa: F401

            return True
        except ImportError:
            return False

    def encode(self, text: str) -> list[float] | None:
        """Synchronously encode *text* and return a 384-dimensional vector.

        Returns ``None`` for empty/None input or if the library is not
        installed.
        """
        if text is None or not text or not text.strip():
            log.warning("local_embedding_empty_text")
            return None

        model = self._load_model()
        if model is None:
            return None

        try:
            vector = model.encode(text, convert_to_numpy=True)
            result: list[float] = vector.tolist()
            log.info(
                "local_embedding_generated",
                text_length=len(text),
                embedding_dim=len(result),
                model=self._model_name,
            )
            return result
        except Exception as e:
            log.error("local_embedding_encode_failed", error=str(e))
            return None

    # ------------------------------------------------------------------
    # BaseEmbeddingProvider interface
    # ------------------------------------------------------------------

    async def generate_embedding(self, text: str) -> list[float] | None:
        """Async wrapper around :meth:`encode` (sentence-transformers is sync)."""
        return self.encode(text)

    def embedding_dimensions(self) -> int:
        """Return 384 – the dimension of all-MiniLM-L6-v2."""
        return 384

    def provider_name(self) -> str:
        """Return provider name."""
        return "local"

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_model(self):
        """Load (or return cached) SentenceTransformer model."""
        global _local_st_model

        if _local_st_model is not None:
            return _local_st_model

        if not self.is_importable():
            log.error(
                "sentence_transformers_not_installed",
                hint="pip install sentence-transformers",
            )
            return None

        try:
            from sentence_transformers import SentenceTransformer

            log.info(
                "loading_local_embedding_model",
                model=self._model_name,
                cache_folder=self._cache_folder,
            )
            _local_st_model = SentenceTransformer(
                self._model_name,
                cache_folder=self._cache_folder,
            )
            return _local_st_model
        except Exception as e:
            log.error("local_model_load_failed", model=self._model_name, error=str(e))
            return None


def get_embedding_provider() -> BaseEmbeddingProvider:
    """Factory function to get configured embedding provider.

    Returns:
        Configured embedding provider instance

    Raises:
        ValueError: If provider is unknown
    """
    provider = settings.RAG_EMBEDDING_PROVIDER.lower()

    if provider == "ollama":
        return OllamaEmbeddingProvider()
    elif provider == "openai":
        return OpenAIEmbeddingProvider()
    elif provider == "local":
        return LocalEmbeddingProvider()
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")
