"""Weather and agronomic provider catalog for PR721 integration.

Only OpenMeteo is actively queried by default. The remaining providers are
registered as capability descriptors so the product can represent the full
Phase-2 provider inventory without inventing live data.
"""

from __future__ import annotations

import os
from typing import Any

from app.providers.peru_intel import fetch_openmeteo_weather

DISPLAY_TO_PROVIDER_REGION = {
    "Cajamarca": "Cajamarca",
    "Junin": "Jun\xc3\xadn",
    "San Martin": "San Mart\xc3\xadn",
    "Cusco": "Cusco",
    "Amazonas": "Amazonas",
    "Puno": "Puno",
}


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


class OpenMeteoProvider:
    SOURCE_NAME = "OpenMeteo"

    @staticmethod
    def provider_status() -> dict[str, Any]:
        return _provider_entry(
            name=OpenMeteoProvider.SOURCE_NAME,
            group="weather",
            mode="active",
            configured=True,
            coverage="Peru coffee regions",
            notes="Primary live weather source without API key.",
        )

    @staticmethod
    def fetch_region_weather(region: str) -> dict[str, Any] | None:
        provider_region = DISPLAY_TO_PROVIDER_REGION.get(region, region)
        weather = fetch_openmeteo_weather(provider_region)
        if not weather:
            return None

        return {
            "region": region,
            "temperature_c": weather.current_temp_c,
            "temp_max_c": weather.temp_max_c,
            "temp_min_c": weather.temp_min_c,
            "precipitation_mm": weather.precipitation_mm,
            "observed_at": weather.observed_at.isoformat(),
            "source": weather.source_name,
            "metadata": weather.metadata,
        }

    @staticmethod
    def fetch_all_regions() -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for region in DISPLAY_TO_PROVIDER_REGION:
            payload = OpenMeteoProvider.fetch_region_weather(region)
            if payload:
                rows.append(payload)
        return rows


class WeatherbitProvider:
    SOURCE_NAME = "Weatherbit"

    @staticmethod
    def provider_status() -> dict[str, Any]:
        return _provider_entry(
            name=WeatherbitProvider.SOURCE_NAME,
            group="agronomic",
            mode="optional",
            configured=bool(os.getenv("WEATHERBIT_API_KEY")),
            coverage="Soil moisture and ET",
            notes="Optional agronomic enrichment source.",
        )


class NASAGPMProvider:
    SOURCE_NAME = "NASA GPM"

    @staticmethod
    def provider_status() -> dict[str, Any]:
        return _provider_entry(
            name=NASAGPMProvider.SOURCE_NAME,
            group="agronomic",
            mode="public",
            configured=True,
            coverage="Global precipitation reference",
            notes="Public archive, not yet part of the critical daily ingest path.",
        )


class RAIN4PEProvider:
    SOURCE_NAME = "RAIN4PE"

    @staticmethod
    def provider_status() -> dict[str, Any]:
        return _provider_entry(
            name=RAIN4PEProvider.SOURCE_NAME,
            group="agronomic",
            mode="archive",
            configured=True,
            coverage="Peru precipitation archive",
            notes="Historical source reserved for backfill and analysis.",
        )


class WeatherProvider:
    @staticmethod
    def provider_catalog() -> list[dict[str, Any]]:
        return [
            OpenMeteoProvider.provider_status(),
            WeatherbitProvider.provider_status(),
            NASAGPMProvider.provider_status(),
            RAIN4PEProvider.provider_status(),
        ]

    @staticmethod
    def fetch_all_weather() -> list[dict[str, Any]]:
        return OpenMeteoProvider.fetch_all_regions()
