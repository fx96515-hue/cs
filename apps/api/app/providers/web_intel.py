"""Web intelligence provider using Perplexity Sonar API.

Provides structured web research capabilities for data that doesn't have
direct APIs available.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Any

import httpx
import structlog

log = structlog.get_logger()


@dataclass(frozen=True)
class WebIntelligence:
    """Structured web intelligence result."""

    query: str
    content: str
    citations: list[str]
    observed_at: datetime
    source_name: str
    raw_data: str
    metadata: dict


def research_topic(
    query: str,
    perplexity_api_key: Optional[str],
    max_tokens: int = 1000,
    temperature: float = 0.2,
    timeout_s: float = 60.0,
) -> Optional[WebIntelligence]:
    """Research a topic using Perplexity Sonar API.

    Perplexity Sonar provides AI-powered web search and synthesis,
    useful for gathering data when no direct API exists.

    Args:
        query: Research query
        perplexity_api_key: Perplexity API key (required)
        max_tokens: Maximum response tokens
        temperature: Response temperature (0-1, lower = more focused)
        timeout_s: Request timeout

    Returns:
        WebIntelligence with structured data, or None on failure
    """
    if not perplexity_api_key:
        log.warning(
            "perplexity_no_api_key",
            query=query[:100],
            note="PERPLEXITY_API_KEY not configured",
        )
        return None

    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {perplexity_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a research assistant. Provide accurate, "
                    "well-sourced information based on current web data."
                ),
            },
            {"role": "user", "content": query},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        r = httpx.post(url, headers=headers, json=payload, timeout=timeout_s)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log.warning(
            "perplexity_research_failed",
            query=query[:100],
            error=str(e),
            exc_info=True,
        )
        return None

    try:
        choices = data.get("choices", [])
        if not choices:
            log.warning("perplexity_no_choices", query=query[:100])
            return None

        message = choices[0].get("message", {})
        content = message.get("content", "")
        citations = data.get("citations", [])

        if not content:
            log.warning("perplexity_no_content", query=query[:100])
            return None

        return WebIntelligence(
            query=query,
            content=content,
            citations=citations,
            observed_at=datetime.now(timezone.utc),
            source_name="Perplexity Sonar",
            raw_data=json.dumps(data),
            metadata={
                "model": payload["model"],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "usage": data.get("usage", {}),
            },
        )
    except Exception as e:
        log.warning(
            "perplexity_parse_failed",
            query=query[:100],
            error=str(e),
            exc_info=True,
        )
        return None


def research_ico_price(perplexity_api_key: Optional[str]) -> Optional[dict[str, Any]]:
    """Research current ICO coffee prices using Perplexity.

    Args:
        perplexity_api_key: Perplexity API key

    Returns:
        Dictionary with ICO price intelligence
    """
    query = (
        "What is the current ICO (International Coffee Organization) "
        "Composite Indicator price for Arabica coffee? Provide the price "
        "in USD per pound, the date, and source."
    )

    intel = research_topic(
        query=query,
        perplexity_api_key=perplexity_api_key,
        max_tokens=500,
        temperature=0.1,
    )

    if not intel:
        return None

    return {
        "source": "ICO via Perplexity",
        "available": True,
        "content": intel.content,
        "citations": intel.citations,
        "observed_at": intel.observed_at.isoformat(),
        "note": "ICO price intelligence from web research",
    }
