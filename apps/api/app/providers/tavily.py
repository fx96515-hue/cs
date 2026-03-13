from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.core.config import settings


class TavilyError(RuntimeError):
    pass


@dataclass
class TavilySearchResult:
    title: str
    url: str
    snippet: str | None = None
    raw_content: str | None = None


class TavilyClient:
    """Minimal Tavily Search API wrapper for deep discovery mode."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_s: Optional[int] = None,
    ):
        self.api_key = api_key or settings.TAVILY_API_KEY
        self.base_url = (base_url or settings.TAVILY_BASE_URL).rstrip("/")
        self.timeout_s = timeout_s or settings.TAVILY_TIMEOUT_SECONDS

        if not self.api_key:
            raise TavilyError(
                "TAVILY_API_KEY fehlt. Setze ihn in .env oder als Umgebungsvariable."
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
        query: str,
        *,
        max_results: int = 10,
        country: str | None = None,
        search_depth: str = "basic",
        include_raw_content: str | bool = False,
    ) -> list[TavilySearchResult]:
        payload: dict[str, object] = {
            "query": query,
            "topic": "general",
            "max_results": max_results,
            "search_depth": search_depth,
            "include_raw_content": include_raw_content,
        }
        if country:
            payload["country"] = country

        resp = self._client.post("/search", json=payload)
        if resp.status_code >= 400:
            raise TavilyError(f"Tavily /search error {resp.status_code}: {resp.text}")

        data = resp.json()
        results: list[TavilySearchResult] = []
        for item in data.get("results", []) or []:
            url = str(item.get("url") or "").strip()
            title = str(item.get("title") or "").strip()
            if not url or not title:
                continue
            results.append(
                TavilySearchResult(
                    title=title,
                    url=url,
                    snippet=item.get("content"),
                    raw_content=item.get("raw_content"),
                )
            )
        return results
