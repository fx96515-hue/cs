"""Peru macro and trade provider catalog for PR721 integration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.providers.peru_intel import fetch_ico_price_data


def _provider_entry(
    *,
    name: str,
    group: str,
    mode: str,
    configured: bool,
    coverage: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "group": group,
        "mode": mode,
        "configured": configured,
        "coverage": coverage,
        "notes": notes,
    }


class INEIProvider:
    SOURCE_NAME = "INEI Peru"

    @staticmethod
    def provider_status() -> dict[str, Any]:
        return _provider_entry(
            name=INEIProvider.SOURCE_NAME,
            group="macro",
            mode="reference",
            configured=True,
            coverage="Peru production statistics",
            notes="Reference data source for national agriculture statistics.",
        )


class WorldBankWITSProvider:
    SOURCE_NAME = "World Bank WITS"

    @staticmethod
    def provider_status() -> dict[str, Any]:
        return _provider_entry(
            name=WorldBankWITSProvider.SOURCE_NAME,
            group="macro",
            mode="reference",
            configured=True,
            coverage="Trade and export statistics",
            notes="Reference source for trade flows and export volumes.",
        )


class BCRPProvider:
    SOURCE_NAME = "BCRP Peru"

    @staticmethod
    def provider_status() -> dict[str, Any]:
        return _provider_entry(
            name=BCRPProvider.SOURCE_NAME,
            group="macro",
            mode="reference",
            configured=True,
            coverage="FX and macro indicators",
            notes="Central-bank reference for Peru macro context.",
        )


class ICOProvider:
    SOURCE_NAME = "ICO"

    @staticmethod
    def provider_status() -> dict[str, Any]:
        return _provider_entry(
            name=ICOProvider.SOURCE_NAME,
            group="macro",
            mode="active",
            configured=True,
            coverage="Coffee market benchmarks",
            notes="Available through the current fallback benchmark implementation.",
        )

    @staticmethod
    def fetch_reference_snapshot() -> dict[str, Any]:
        payload = fetch_ico_price_data()
        return {
            "source": ICOProvider.SOURCE_NAME,
            "available": payload.get("available", False),
            "data": payload.get("data", {}),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }


class CoffeeResearchProvider:
    SOURCE_NAME = "Coffee Research"

    @staticmethod
    def provider_status() -> dict[str, Any]:
        return _provider_entry(
            name=CoffeeResearchProvider.SOURCE_NAME,
            group="macro",
            mode="reference",
            configured=True,
            coverage="Quality and agronomy reference",
            notes="Reference source for standards, quality and varietal context.",
        )


class MacroProvider:
    @staticmethod
    def provider_catalog() -> list[dict[str, Any]]:
        return [
            INEIProvider.provider_status(),
            WorldBankWITSProvider.provider_status(),
            BCRPProvider.provider_status(),
            ICOProvider.provider_status(),
            CoffeeResearchProvider.provider_status(),
        ]

    @staticmethod
    def fetch_all_macro_data() -> dict[str, Any]:
        return {
            "providers": MacroProvider.provider_catalog(),
            "ico_reference": ICOProvider.fetch_reference_snapshot(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
