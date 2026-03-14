from __future__ import annotations

from types import SimpleNamespace

from app.models.cooperative import Cooperative
from app.models.source import Source
from app.services import discovery as discovery_service


class _FakeTavilyClient:
    def __init__(self, *args, **kwargs):
        pass

    def search(self, query: str, *, max_results: int = 10, country: str | None = None):
        return [
            SimpleNamespace(
                title="Cooperativa Valle Verde | Specialty Coffee Peru",
                url="https://example.org/coop/valle-verde",
                snippet="Peru cooperative with export program.",
            ),
            SimpleNamespace(
                title="Cooperativa Valle Verde | Export Details",
                url="https://example.org/coop/valle-verde/export",
                snippet="Exports specialty lots to EU buyers.",
            ),
        ]

    def close(self):
        return None


def test_seed_discovery_requires_provider(db, monkeypatch):
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    result = discovery_service.seed_discovery(
        db,
        entity_type="cooperative",
        max_entities=5,
    )

    assert result["created"] == 0
    assert result["provider"] is None
    assert result["errors"]
    assert "No discovery provider configured" in result["errors"][0]


def test_seed_discovery_uses_tavily_fallback(db, monkeypatch):
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    monkeypatch.setattr(discovery_service, "TavilyClient", _FakeTavilyClient)

    result = discovery_service.seed_discovery(
        db,
        entity_type="cooperative",
        max_entities=10,
    )

    assert result["provider"] == "tavily"
    assert result["created"] >= 1
    assert result["errors"] == []

    coop = db.query(Cooperative).filter_by(name="Cooperativa Valle Verde").first()
    assert coop is not None
    assert (coop.meta or {}).get("discovery", {}).get("provider") == "tavily"

    src = db.query(Source).filter_by(name="Tavily Discovery").first()
    assert src is not None
