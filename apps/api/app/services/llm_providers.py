"""LLM Provider abstraction for multi-provider support.

Supports Ollama (local, no API key), OpenAI, and Groq providers.
"""

from __future__ import annotations

import inspect
import json
import structlog
from abc import ABC, abstractmethod
from typing import AsyncIterator

import httpx

from app.core.config import settings

log = structlog.get_logger()


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def chat_completion(
        self, messages: list[dict], temperature: float, model: str
    ) -> dict:
        """Send chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            model: Model name/ID

        Returns:
            Dict with 'content' (str) and 'tokens_used' (int | None)
        """
        raise NotImplementedError

    async def stream_chat_completion(
        self, messages: list[dict], temperature: float, model: str
    ) -> AsyncIterator[str]:
        """Stream chat completion tokens.

        Default implementation fetches the full response and yields it in one chunk.
        Providers that support native streaming should override this.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            model: Model name/ID

        Yields:
            Text chunks of the assistant response
        """
        result = await self.chat_completion(
            messages=messages, temperature=temperature, model=model
        )
        yield result["content"]

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        raise NotImplementedError

    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name."""
        raise NotImplementedError


class OllamaProvider(BaseLLMProvider):
    """Ollama provider - runs locally, no API key needed."""

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL
        self.timeout = 120.0  # Ollama can be slower for large models

    async def chat_completion(
        self, messages: list[dict], temperature: float, model: str
    ) -> dict:
        """Send chat completion to Ollama.

        Args:
            messages: Chat messages
            temperature: Sampling temperature
            model: Ollama model name (e.g., 'llama3.1:8b')

        Returns:
            Dict with content and tokens_used

        Raises:
            Exception: If Ollama is unavailable or request fails
        """
        try:
            async with httpx.AsyncClient(trust_env=False) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": temperature},
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                if inspect.isawaitable(data):
                    data = await data

                content = data["message"]["content"]
                tokens_used = data.get("eval_count")

                log.info(
                    "ollama_chat_completion",
                    model=model,
                    tokens=tokens_used,
                    content_length=len(content),
                )

                return {"content": content, "tokens_used": tokens_used}

        except httpx.HTTPStatusError as e:
            log.error(
                "ollama_api_error",
                status_code=e.response.status_code,
                error=str(e),
            )
            raise RuntimeError(
                f"Ollama API error: {e.response.status_code}. "
                "Stellen Sie sicher, dass Ollama läuft: ollama serve"
            )
        except httpx.ConnectError as e:
            log.error("ollama_connection_error", error=str(e))
            raise ConnectionError(
                "Ollama nicht erreichbar. Starten Sie Ollama mit: ollama serve"
            )
        except Exception as e:
            log.error("ollama_chat_completion_failed", error=str(e))
            if "connection refused" in str(e).lower():
                raise ConnectionError(
                    "Ollama nicht erreichbar. Starten Sie Ollama mit: ollama serve"
                )
            raise

    async def stream_chat_completion(
        self, messages: list[dict], temperature: float, model: str
    ) -> AsyncIterator[str]:
        """Stream chat completion from Ollama (native streaming).

        Args:
            messages: Chat messages
            temperature: Sampling temperature
            model: Ollama model name

        Yields:
            Text chunks of the assistant response
        """
        try:
            async with httpx.AsyncClient(trust_env=False) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": True,
                        "options": {"temperature": temperature},
                    },
                    timeout=self.timeout,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            chunk = data.get("message", {}).get("content", "")
                            if chunk:
                                yield chunk
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            log.error("ollama_stream_failed", error=str(e))
            raise

    def is_available(self) -> bool:
        """Check if Ollama is reachable.

        Returns:
            True if Ollama responds to /api/tags
        """
        try:
            response = httpx.get(
                f"{self.base_url}/api/tags", timeout=5.0, trust_env=False
            )
            return response.status_code == 200
        except Exception as e:
            log.debug("ollama_availability_check_failed", error=str(e))
            return False

    def provider_name(self) -> str:
        """Return provider name."""
        return "ollama"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider - requires OPENAI_API_KEY."""

    def __init__(self) -> None:
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.timeout = 60.0

    async def chat_completion(
        self, messages: list[dict], temperature: float, model: str
    ) -> dict:
        """Send chat completion to OpenAI.

        Args:
            messages: Chat messages
            temperature: Sampling temperature
            model: OpenAI model name (e.g., 'gpt-4o-mini')

        Returns:
            Dict with content and tokens_used

        Raises:
            Exception: If API key missing or request fails
        """
        if not self.is_available():
            raise ValueError("OpenAI API key not configured")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                if inspect.isawaitable(data):
                    data = await data

                content = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens")

                log.info(
                    "openai_chat_completion",
                    model=model,
                    tokens=tokens_used,
                    content_length=len(content),
                )

                return {"content": content, "tokens_used": tokens_used}

        except httpx.HTTPStatusError as e:
            log.error(
                "openai_api_error",
                status_code=e.response.status_code,
                error=str(e),
            )
            raise RuntimeError(f"OpenAI API error: {e.response.status_code}")
        except Exception as e:
            log.error("openai_chat_completion_failed", error=str(e))
            raise

    async def stream_chat_completion(
        self, messages: list[dict], temperature: float, model: str
    ) -> AsyncIterator[str]:
        """Stream chat completion from OpenAI (native streaming).

        Args:
            messages: Chat messages
            temperature: Sampling temperature
            model: OpenAI model name

        Yields:
            Text chunks of the assistant response
        """
        if not self.is_available():
            raise ValueError("OpenAI API key not configured")

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "stream": True,
                    },
                    timeout=self.timeout,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        payload = line[6:]
                        if payload.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(payload)
                            chunk = (
                                data.get("choices", [{}])[0]
                                .get("delta", {})
                                .get("content", "")
                            )
                            if chunk:
                                yield chunk
                        except (json.JSONDecodeError, IndexError):
                            continue
        except Exception as e:
            log.error("openai_stream_failed", error=str(e))
            raise

    def is_available(self) -> bool:
        """Check if OpenAI API key is configured.

        Returns:
            True if API key is set
        """
        return self.api_key is not None and len(self.api_key.strip()) > 0

    def provider_name(self) -> str:
        """Return provider name."""
        return "openai"


class GroqProvider(BaseLLMProvider):
    """Groq provider - free API key, very fast inference."""

    def __init__(self) -> None:
        self.api_key = settings.GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.timeout = 30.0  # Groq is typically fast

    async def chat_completion(
        self, messages: list[dict], temperature: float, model: str
    ) -> dict:
        """Send chat completion to Groq.

        Args:
            messages: Chat messages
            temperature: Sampling temperature
            model: Groq model name (e.g., 'llama-3.1-8b-instant')

        Returns:
            Dict with content and tokens_used

        Raises:
            Exception: If API key missing or request fails
        """
        if not self.is_available():
            raise ValueError("Groq API key not configured")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                if inspect.isawaitable(data):
                    data = await data

                content = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens")

                log.info(
                    "groq_chat_completion",
                    model=model,
                    tokens=tokens_used,
                    content_length=len(content),
                )

                return {"content": content, "tokens_used": tokens_used}

        except httpx.HTTPStatusError as e:
            log.error(
                "groq_api_error",
                status_code=e.response.status_code,
                error=str(e),
            )
            raise RuntimeError(f"Groq API error: {e.response.status_code}")
        except Exception as e:
            log.error("groq_chat_completion_failed", error=str(e))
            raise

    async def stream_chat_completion(
        self, messages: list[dict], temperature: float, model: str
    ) -> AsyncIterator[str]:
        """Stream chat completion from Groq (native streaming).

        Args:
            messages: Chat messages
            temperature: Sampling temperature
            model: Groq model name

        Yields:
            Text chunks of the assistant response
        """
        if not self.is_available():
            raise ValueError("Groq API key not configured")

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "stream": True,
                    },
                    timeout=self.timeout,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        payload = line[6:]
                        if payload.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(payload)
                            chunk = (
                                data.get("choices", [{}])[0]
                                .get("delta", {})
                                .get("content", "")
                            )
                            if chunk:
                                yield chunk
                        except (json.JSONDecodeError, IndexError):
                            continue
        except Exception as e:
            log.error("groq_stream_failed", error=str(e))
            raise

    def is_available(self) -> bool:
        """Check if Groq API key is configured.

        Returns:
            True if API key is set
        """
        return self.api_key is not None and len(self.api_key.strip()) > 0

    def provider_name(self) -> str:
        """Return provider name."""
        return "groq"


class DeterministicFallbackProvider(BaseLLMProvider):
    """Local fallback provider that produces deterministic summaries."""

    def _build_fallback_response(self, messages: list[dict]) -> str:
        user_message = ""
        system_prompt = ""

        for message in messages:
            role = message.get("role")
            if role == "system" and not system_prompt:
                system_prompt = str(message.get("content") or "")
            if role == "user":
                user_message = str(message.get("content") or "")

        context_lines: list[str] = []
        for raw_line in system_prompt.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("**") or line.startswith("- ") or line.startswith("## "):
                context_lines.append(line)
            if len(context_lines) >= 10:
                break

        answer_lines = [
            "Der konfigurierte KI-Provider ist derzeit nicht erreichbar.",
            "Ich liefere deshalb eine lokale, deterministische Zusammenfassung aus den vorhandenen Daten.",
        ]
        if user_message:
            answer_lines.append(f"Frage: {user_message}")

        if context_lines:
            answer_lines.append("")
            answer_lines.append("Verfuegbare Hinweise:")
            answer_lines.extend(context_lines)
        else:
            answer_lines.append("")
            answer_lines.append(
                "Es sind aktuell keine strukturierten Kontextdaten verfuegbar."
            )

        answer_lines.append("")
        answer_lines.append(
            "Fuer eine frei formulierte KI-Antwort kann spaeter wieder ein echter LLM-Provider aktiviert werden."
        )
        return "\n".join(answer_lines)

    async def chat_completion(
        self, messages: list[dict], temperature: float, model: str
    ) -> dict:
        content = self._build_fallback_response(messages)
        return {"content": content, "tokens_used": None}

    def is_available(self) -> bool:
        return True

    def provider_name(self) -> str:
        return "deterministic_fallback"


def get_llm_provider() -> BaseLLMProvider:
    """Factory function to get configured LLM provider.

    Returns:
        Configured LLM provider instance

    Raises:
        ValueError: If provider is unknown
    """
    provider = settings.RAG_PROVIDER.lower()

    if provider == "ollama":
        selected: BaseLLMProvider = OllamaProvider()
    elif provider == "openai":
        selected = OpenAIProvider()
    elif provider == "groq":
        selected = GroqProvider()
    else:
        raise ValueError(f"Unknown RAG provider: {provider}")

    if selected.is_available():
        return selected

    log.warning(
        "llm_provider_fallback_enabled",
        configured_provider=provider,
    )
    return DeterministicFallbackProvider()
