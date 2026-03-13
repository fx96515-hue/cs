from types import SimpleNamespace
from unittest.mock import patch

from app.providers.perplexity import PerplexityError
from app.services.discovery import seed_discovery


class _FailingPerplexityClient:
    def search(self, *args, **kwargs):
        raise PerplexityError("Perplexity /search error 401: insufficient_quota")

    def close(self):
        return None


class _StubTavilyClient:
    def search(self, *args, **kwargs):
        return [
            SimpleNamespace(
                title="Bonanza Coffee Roasters | Specialty Coffee in Berlin",
                url="https://bonanzacoffee.de",
                snippet="Specialty coffee roastery in Berlin with Peru offerings.",
                raw_content="Bonanza Coffee Roasters sources specialty coffees and features Peru lots.",
            )
        ]

    def close(self):
        return None


def test_seed_discovery_uses_tavily_when_perplexity_quota_exceeded(db):
    with (
        patch("app.services.discovery.settings.TAVILY_API_KEY", "tvly-test"),
        patch("app.services.discovery.settings.DISCOVERY_DEMO_FALLBACK_ENABLED", False),
        patch("app.services.discovery.PerplexityClient", return_value=_FailingPerplexityClient()),
        patch("app.services.discovery.TavilyClient", return_value=_StubTavilyClient()),
    ):
        result = seed_discovery(
            db,
            entity_type="roaster",
            mode="deep",
            max_entities=5,
            dry_run=True,
            country_filter="DE",
        )

    assert result["mode"] == "deep"
    assert result["provider"] == "tavily"
    assert result["provider_status"] == "heuristic_tavily"
    assert result["search_providers"] == ["tavily"]
    assert result["created"] == 1
    assert result["fallback"] is None
