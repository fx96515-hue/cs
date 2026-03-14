"""PR721 Phase-2 compatibility facade."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.providers.news_market import NewsProvider
from app.providers.peru_macro import MacroProvider
from app.providers.shipping_data import ShippingProvider
from app.providers.weather import WeatherProvider


class Phase2DataPipelineFacade:
    SOURCE_GROUPS = {
        "market": ["coffee_prices", "fx_rates", "freight_rates"],
        "weather": ["openmeteo", "weatherbit", "nasa_gpm", "rain4pe"],
        "shipping": ["ais_stream", "marinetraffic"],
        "news": ["newsapi", "twitter_sentiment", "reddit_sentiment", "web_research"],
        "macro": ["inei", "wits", "bcrp", "ico", "coffee_research"],
    }

    @staticmethod
    def provider_catalog() -> list[dict[str, Any]]:
        catalog: list[dict[str, Any]] = [
            {
                "name": "Yahoo Finance / Stooq",
                "group": "market",
                "mode": "active",
                "configured": True,
                "coverage": "Coffee futures and fallback benchmarks",
                "notes": "Existing production market price chain.",
            },
            {
                "name": "ECB / ExchangeRate / Frankfurter",
                "group": "market",
                "mode": "active",
                "configured": True,
                "coverage": "FX rates",
                "notes": "Existing production FX fallback chain.",
            },
        ]
        catalog.extend(WeatherProvider.provider_catalog())
        catalog.extend(ShippingProvider.provider_catalog())
        catalog.extend(NewsProvider.provider_catalog())
        catalog.extend(MacroProvider.provider_catalog())
        return catalog

    @classmethod
    def provider_summary(cls) -> dict[str, Any]:
        catalog = cls.provider_catalog()
        groups = Counter(entry["group"] for entry in catalog)
        active = sum(1 for entry in catalog if entry["mode"] == "active")
        optional = sum(1 for entry in catalog if entry["mode"] == "optional")
        return {
            "total_sources": len(catalog),
            "groups": dict(groups),
            "active_sources": active,
            "optional_sources": optional,
        }
