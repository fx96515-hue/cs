"""
Data source implementations for Peru coffee data integration.

Provides real data from:
- OpenMeteo for weather (replaces SENAMHI stub)
- Perplexity for production intelligence (replaces JNC/MINAGRI stubs)
- ICO price fallback data
"""

from typing import Any

from app.core.config import settings
from app.providers.peru_intel import (
    fetch_openmeteo_weather,
    fetch_perplexity_production_intel,
    fetch_ico_price_data as fetch_ico_price_data_impl,
)


def fetch_jnc_data(region_name: str) -> dict[str, Any]:
    """
    Fetch data from Junta Nacional del Café (Peru's National Coffee Board).

    Now uses Perplexity to research current JNC production data.

    Args:
        region_name: Name of the coffee region

    Returns:
        Dictionary with JNC data (from web intelligence)
    """
    intel = fetch_perplexity_production_intel(region_name, settings.PERPLEXITY_API_KEY)

    if intel:
        return {
            "source": "JNC (via Perplexity)",
            "available": True,
            "data": {
                "production_volume_kg": intel.production_volume_kg,
                "export_volume_kg": intel.export_volume_kg,
                "avg_price_usd_kg": intel.avg_price_usd_kg,
                "quality_notes": intel.quality_notes,
            },
            "citations": intel.metadata.get("citations", []),
            "note": "Production intelligence from web research",
        }
    else:
        return {
            "source": "JNC",
            "available": False,
            "data": {},
            "note": "Perplexity API not configured or request failed",
        }


def fetch_minagri_data(region_name: str) -> dict[str, Any]:
    """
    Fetch data from Ministerio de Agricultura y Riego (Peru's Ministry of Agriculture).

    Now uses Perplexity to research MINAGRI agricultural data.

    Args:
        region_name: Name of the coffee region

    Returns:
        Dictionary with MINAGRI data (from web intelligence)
    """
    intel = fetch_perplexity_production_intel(region_name, settings.PERPLEXITY_API_KEY)

    if intel:
        return {
            "source": "MINAGRI (via Perplexity)",
            "available": True,
            "data": {
                "agricultural_stats": intel.quality_notes,
                "region": region_name,
            },
            "citations": intel.metadata.get("citations", []),
            "note": "Agricultural data from web research",
        }
    else:
        return {
            "source": "MINAGRI",
            "available": False,
            "data": {},
            "note": "Perplexity API not configured or request failed",
        }


def fetch_senamhi_weather(region_name: str) -> dict[str, Any]:
    """
    Fetch weather data from OpenMeteo (replaces SENAMHI).

    OpenMeteo provides free, reliable weather data without requiring API keys.

    Args:
        region_name: Name of the coffee region

    Returns:
        Dictionary with weather data from OpenMeteo
    """
    weather = fetch_openmeteo_weather(region_name)

    if weather:
        return {
            "source": "OpenMeteo",
            "available": True,
            "data": {
                "current_temperature_c": weather.current_temp_c,
                "temperature_max_c": weather.temp_max_c,
                "temperature_min_c": weather.temp_min_c,
                "precipitation_mm": weather.precipitation_mm,
                "observed_at": weather.observed_at.isoformat(),
                "region": region_name,
                "coordinates": weather.metadata.get("latitude"),
            },
            "note": "Real-time weather from OpenMeteo API",
        }
    else:
        return {
            "source": "OpenMeteo",
            "available": False,
            "data": {},
            "note": f"Weather data not available for region: {region_name}",
        }


def fetch_ico_price_data() -> dict[str, Any]:
    """
    Fetch price data from International Coffee Organization (ICO).

    Wraps the peru_intel implementation for backward compatibility.

    Returns:
        Dictionary with ICO price data and fallback values
    """
    return fetch_ico_price_data_impl()


# Export public API
__all__ = [
    "fetch_jnc_data",
    "fetch_minagri_data",
    "fetch_senamhi_weather",
    "fetch_ico_price_data",
]
