from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

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
class TavilyResult:
    title: str
    url: str
    snippet: str | None = None


class TavilyClient:
    """Small wrapper around Tavily Search API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_s: int | None = None,
    ):
        self.api_key = (
            api_key
            or getattr(settings, "TAVILY_API_KEY", None)
            or os.getenv("TAVILY_API_KEY")
        )
        self.base_url = (
            base_url
            or os.getenv("TAVILY_BASE_URL")
            or getattr(settings, "TAVILY_BASE_URL", "https://api.tavily.com")
        ).rstrip("/")
        self.timeout_s = timeout_s or int(
            os.getenv(
                "TAVILY_TIMEOUT_SECONDS",
                str(getattr(settings, "TAVILY_TIMEOUT_SECONDS", 30)),
            )
        )

        if not self.api_key:
            raise TavilyError(
                "TAVILY_API_KEY fehlt. Setze ihn in apps/api/.env oder als Umgebungsvariable."
            )

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout_s, connect=10.0),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    def close(self) -> None:
        self._client.close()

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(initial=1, max=8),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
    )
    def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        country: str | None = None,
    ) -> list[TavilyResult]:
        payload: dict[str, Any] = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
        }
        if country:
            payload["topic"] = "general"

        resp = self._client.post("/search", json=payload)
        if resp.status_code >= 400:
            raise TavilyError(f"Tavily /search error {resp.status_code}: {resp.text}")

        data = resp.json()
        out: list[TavilyResult] = []
        for item in data.get("results", []) or []:
            url = item.get("url")
            title = item.get("title")
            if not url or not title:
                continue
            out.append(
                TavilyResult(
                    title=str(title),
                    url=str(url),
                    snippet=(item.get("content") or item.get("snippet")),
                )
            )
        return out
