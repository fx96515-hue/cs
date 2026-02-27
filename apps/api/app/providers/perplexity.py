from __future__ import annotations

import json
from dataclasses import dataclass
import re
from typing import Any, Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
)

from app.core.config import settings


class PerplexityError(RuntimeError):
    pass


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str | None = None
    date: str | None = None
    last_updated: str | None = None


class PerplexityClient:
    """Small wrapper around Perplexity's API.

    Perplexity supports an OpenAI-compatible Chat Completions API and a dedicated Search API.
    Docs:
      - Search: POST https://api.perplexity.ai/search
      - Chat: POST https://api.perplexity.ai/chat/completions
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_s: Optional[int] = None,
    ):
        self.api_key = api_key or settings.PERPLEXITY_API_KEY
        self.base_url = (base_url or settings.PERPLEXITY_BASE_URL).rstrip("/")
        self.timeout_s = timeout_s or settings.PERPLEXITY_TIMEOUT_SECONDS

        if not self.api_key:
            raise PerplexityError(
                "PERPLEXITY_API_KEY fehlt. Setze ihn in apps/api/.env oder als Umgebungsvariable."
            )

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout_s, connect=10.0),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    def close(self) -> None:
        self._client.close()

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(initial=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
    )
    def search(
        self,
        query: str | list[str],
        *,
        max_results: int = 10,
        country: str | None = None,
        search_domain_filter: list[str] | None = None,
        max_tokens_per_page: int = 512,
    ) -> list[SearchResult]:
        payload: dict[str, Any] = {
            "query": query,
            "max_results": max_results,
            "max_tokens_per_page": max_tokens_per_page,
        }
        if country:
            payload["country"] = country
        if search_domain_filter:
            payload["search_domain_filter"] = search_domain_filter

        resp = self._client.post("/search", json=payload)
        if resp.status_code >= 400:
            raise PerplexityError(
                f"Perplexity /search error {resp.status_code}: {resp.text}"
            )

        data = resp.json()
        results = []
        for r in data.get("results", []) or []:
            if not r.get("url") or not r.get("title"):
                continue
            results.append(
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    snippet=r.get("snippet"),
                    date=r.get("date"),
                    last_updated=r.get("last_updated"),
                )
            )
        return results

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(initial=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
    )
    def chat_completions(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1200,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": model or settings.PERPLEXITY_MODEL_DISCOVERY,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        # Perplexity supports OpenAI-compatible structured outputs via `response_format`.
        # See: https://docs.perplexity.ai/api-reference/chat-completions-post
        if response_format:
            payload["response_format"] = response_format

        resp = self._client.post("/chat/completions", json=payload)
        if resp.status_code >= 400:
            raise PerplexityError(
                f"Perplexity /chat/completions error {resp.status_code}: {resp.text}"
            )
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise PerplexityError(
                f"Unexpected response shape: {json.dumps(data)[:800]}"
            ) from e


def safe_json_loads(text: str) -> Any:
    """Try to parse JSON, forgiving common LLM wrappers.

    We expect the model to return raw JSON, but in practice it may wrap it in
    code fences or add small prefixes. This helper extracts the first JSON
    object/array it can find.
    """
    s = (text or "").strip()

    # 1) Strip fenced blocks ```json ... ``` or ``` ... ```
    if "```" in s:
        # Prefer a ```json fenced block
        m = re.search(
            r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```",
            s,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if m:
            s = m.group(1).strip()
        else:
            # Fallback: remove all fences and keep inner content
            s = re.sub(
                r"```.*?```", lambda mm: mm.group(0).strip("`"), s, flags=re.DOTALL
            )
            s = s.strip().strip("`")

    # 2) Direct parse
    try:
        return json.loads(s)
    except Exception:
        pass

    # 3) Extract first JSON object/array substring
    m = re.search(r"(\{.*\}|\[.*\])", s, flags=re.DOTALL)
    if m:
        return json.loads(m.group(1))

    # 4) Give up with a useful error
    raise ValueError(
        f"Could not parse JSON from model output (first 300 chars): {s[:300]}"
    )
