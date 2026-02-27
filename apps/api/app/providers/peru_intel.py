"""Peru regional intelligence provider.

Provides real data for Peru coffee regions:
- Weather data from OpenMeteo API
- Production/market intelligence from Perplexity
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Any

import httpx
import structlog

log = structlog.get_logger()


# Peru coffee region coordinates for OpenMeteo API
PERU_REGION_COORDS = {
    "Cajamarca": {"lat": -7.16, "lon": -78.52},
    "Junín": {"lat": -11.50, "lon": -75.00},
    "San Martín": {"lat": -6.50, "lon": -76.50},
    "Cusco": {"lat": -13.52, "lon": -71.97},
    "Amazonas": {"lat": -6.23, "lon": -77.87},
    "Puno": {"lat": -14.30, "lon": -69.80},
}


def _safe_float(value: Optional[Any]) -> Optional[float]:
    """Safely convert value to float.

    Args:
        value: Value to convert

    Returns:
        Float value or None if conversion fails
    """
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True)
class WeatherData:
    """Weather data for a region."""

    region_name: str
    current_temp_c: float
    temp_max_c: Optional[float]
    temp_min_c: Optional[float]
    precipitation_mm: Optional[float]
    observed_at: datetime
    source_name: str
    source_url: str
    raw_data: str
    metadata: dict


@dataclass(frozen=True)
class ProductionData:
    """Production/market intelligence for a region."""

    region_name: str
    production_volume_kg: Optional[int]
    export_volume_kg: Optional[int]
    avg_price_usd_kg: Optional[float]
    quality_notes: Optional[str]
    source_name: str
    source_url: str
    raw_data: str
    metadata: dict


def fetch_openmeteo_weather(
    region_name: str, timeout_s: float = 20.0
) -> Optional[WeatherData]:
    """Fetch weather data from OpenMeteo API.

    OpenMeteo provides free weather data without requiring an API key.
    API docs: https://open-meteo.com/en/docs

    Args:
        region_name: Name of Peru region (e.g., "Cajamarca")
        timeout_s: Request timeout

    Returns:
        WeatherData or None if region not found or request fails
    """
    coords = PERU_REGION_COORDS.get(region_name)
    if not coords:
        log.warning("openmeteo_unknown_region", region_name=region_name)
        return None

    lat = coords["lat"]
    lon = coords["lon"]

    url = "https://api.open-meteo.com/v1/forecast"
    # Type the params dict to avoid mypy issues
    request_params: dict[str, str | int | float] = {
        "latitude": str(lat),
        "longitude": str(lon),
        "current_weather": "true",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "America/Lima",
        "forecast_days": 1,
    }

    try:
        r = httpx.get(
            url,
            timeout=timeout_s,
            headers={"User-Agent": "CoffeeStudio/1.0"},
            params=request_params,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log.warning(
            "openmeteo_fetch_failed",
            region_name=region_name,
            error=str(e),
            exc_info=True,
        )
        return None

    try:
        current = data.get("current_weather", {})
        daily = data.get("daily", {})

        current_temp = current.get("temperature")
        if current_temp is None:
            log.warning("openmeteo_no_current_temp", region_name=region_name)
            return None

        # Get daily max/min temps and precipitation
        temp_max = None
        temp_min = None
        precipitation = None

        if daily:
            temp_max_list = daily.get("temperature_2m_max", [])
            temp_min_list = daily.get("temperature_2m_min", [])
            precip_list = daily.get("precipitation_sum", [])

            if temp_max_list:
                temp_max = _safe_float(temp_max_list[0])
            if temp_min_list:
                temp_min = _safe_float(temp_min_list[0])
            if precip_list:
                precipitation = _safe_float(precip_list[0])

        # Parse timestamp
        time_str = current.get("time")
        if time_str:
            try:
                observed_at = datetime.fromisoformat(time_str).replace(
                    tzinfo=timezone.utc
                )
            except Exception:
                observed_at = datetime.now(timezone.utc)
        else:
            observed_at = datetime.now(timezone.utc)

        return WeatherData(
            region_name=region_name,
            current_temp_c=float(current_temp),
            temp_max_c=temp_max,
            temp_min_c=temp_min,
            precipitation_mm=precipitation,
            observed_at=observed_at,
            source_name="OpenMeteo",
            source_url=url,
            raw_data=json.dumps(data),
            metadata={
                "latitude": lat,
                "longitude": lon,
                "timezone": data.get("timezone", "America/Lima"),
                "windspeed": current.get("windspeed"),
                "weathercode": current.get("weathercode"),
            },
        )
    except Exception as e:
        log.warning(
            "openmeteo_parse_failed",
            region_name=region_name,
            error=str(e),
            exc_info=True,
        )
        return None


def fetch_perplexity_production_intel(
    region_name: str, perplexity_api_key: Optional[str], timeout_s: float = 60.0
) -> Optional[ProductionData]:
    """Fetch production intelligence using Perplexity Sonar API.

    Uses Perplexity's web search capabilities to gather current production
    and market data for Peru coffee regions.

    Args:
        region_name: Name of Peru region
        perplexity_api_key: Perplexity API key (required)
        timeout_s: Request timeout

    Returns:
        ProductionData or None if API key missing or request fails
    """
    if not perplexity_api_key:
        log.warning(
            "perplexity_no_api_key",
            region_name=region_name,
            note="PERPLEXITY_API_KEY not configured",
        )
        return None

    current_year = datetime.now().year
    query = (
        f"Peru {region_name} coffee production volume export statistics "
        f"{current_year}. Provide production volume in kg, export volume, "
        f"average price per kg, and quality characteristics."
    )

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
                "content": "You are a coffee industry data analyst. Provide structured data about coffee production.",
            },
            {"role": "user", "content": query},
        ],
        "temperature": 0.2,
        "max_tokens": 500,
    }

    try:
        r = httpx.post(url, headers=headers, json=payload, timeout=timeout_s)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log.warning(
            "perplexity_fetch_failed",
            region_name=region_name,
            error=str(e),
            exc_info=True,
        )
        return None

    try:
        choices = data.get("choices", [])
        if not choices:
            log.warning("perplexity_no_choices", region_name=region_name)
            return None

        content = choices[0].get("message", {}).get("content", "")
        citations = data.get("citations", [])

        # Parse the response (simple extraction - could be enhanced with structured output)
        # For now, just store the raw intelligence
        return ProductionData(
            region_name=region_name,
            production_volume_kg=None,  # Would need structured parsing
            export_volume_kg=None,
            avg_price_usd_kg=None,
            quality_notes=content[:500] if content else None,
            source_name="Perplexity Sonar",
            source_url=url,
            raw_data=json.dumps(data),
            metadata={
                "query": query,
                "citations": citations[:5] if citations else [],
                "model": payload["model"],
            },
        )
    except Exception as e:
        log.warning(
            "perplexity_parse_failed",
            region_name=region_name,
            error=str(e),
            exc_info=True,
        )
        return None


def fetch_ico_price_data() -> dict[str, Any]:
    """Fetch ICO price data (fallback implementation).

    This provides static fallback prices based on historical ICO data.
    In the future, this could scrape ico.org or use Perplexity to find current prices.

    Returns:
        Dictionary with ICO price data and fallback values
    """
    return {
        "source": "ICO",
        "available": True,
        "fallback_prices": {
            "arabica_mild": {
                "price_usd_per_lb": 2.10,
                "note": "Historical ICO Composite Indicator average",
            },
            "peru_fob_benchmark": {
                "price_usd_per_kg": 4.85,
                "note": "Estimated from regional FOB averages",
            },
        },
        "data": {
            "composite_indicator": {
                "arabica_mild": 2.10,
                "other_milds": 2.15,
                "robusta": 1.45,
            },
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "note": "Static fallback - live ICO integration pending",
        },
    }
