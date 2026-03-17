"""
Peru Region Intelligence Service.

Provides comprehensive intelligence on Peru coffee regions including:
- Growing conditions scoring
- Production data
- Infrastructure assessment
- External data integration
"""

import unicodedata
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.region import Region
from app.services.data_sources.peru_data_sources import (
    fetch_jnc_data,
    fetch_minagri_data,
    fetch_senamhi_weather,
)


class PeruRegionIntelService:
    """Service for Peru region intelligence and analysis."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _normalize_region_name(value: str) -> str:
        """Normalize region names for robust matching.

        Handles frontend display names like "Junín (Satipo/Chanchamayo)" by
        removing parenthetical qualifiers and diacritics.
        """
        raw = (value or "").strip()
        base = raw
        # Remove a trailing "(...)" suffix without regex backtracking risks.
        open_idx = raw.rfind("(")
        if open_idx != -1 and raw.endswith(")"):
            base = raw[:open_idx].rstrip()
        no_diacritics = "".join(
            ch
            for ch in unicodedata.normalize("NFKD", base)
            if not unicodedata.combining(ch)
        )
        return " ".join(no_diacritics.split()).lower()

    def _resolve_region(self, region_name: str) -> Region | None:
        """Resolve a Peru region by exact or normalized alias name."""
        exact_stmt = select(Region).where(
            Region.name == region_name, Region.country == "Peru"
        )
        exact_region = self.db.scalar(exact_stmt)
        if exact_region:
            return exact_region

        target = self._normalize_region_name(region_name)
        stmt = select(Region).where(Region.country == "Peru")
        regions = self.db.scalars(stmt).all()
        for region in regions:
            if self._normalize_region_name(region.name) == target:
                return region
        return None

    def get_region_intelligence(self, region_name: str) -> dict[str, Any] | None:
        """
        Get comprehensive intelligence for a Peru coffee region.

        Args:
            region_name: Name of the region (e.g., "Cajamarca", "Junín")

        Returns:
            Dictionary with region intelligence or None if not found
        """
        region = self._resolve_region(region_name)

        if not region:
            return None

        # Calculate growing conditions score
        growing_score = self.calculate_growing_conditions_score(region)

        return {
            "name": region.name,
            "country": region.country,
            "description": region.description,
            "elevation_range": {
                "min_m": region.elevation_min_m,
                "max_m": region.elevation_max_m,
            },
            "climate": {
                "avg_temperature_c": region.avg_temperature_c,
                "rainfall_mm": region.rainfall_mm,
                "humidity_pct": region.humidity_pct,
            },
            "soil_type": region.soil_type,
            "production": {
                "volume_kg": region.production_volume_kg,
                "share_pct": region.production_share_pct,
                "harvest_months": region.harvest_months,
            },
            "quality": {
                "typical_varieties": region.typical_varieties,
                "typical_processing": region.typical_processing,
                "profile": region.quality_profile,
                "consistency_score": region.quality_consistency_score,
            },
            "logistics": {
                "main_port": region.main_port,
                "transport_time_hours": region.transport_time_hours,
                "cost_per_kg": region.logistics_cost_per_kg,
                "infrastructure_score": region.infrastructure_score,
            },
            "risks": {
                "weather": region.weather_risk,
                "political": region.political_risk,
                "logistics": region.logistics_risk,
            },
            "scores": {
                "growing_conditions": growing_score,
                "infrastructure": region.infrastructure_score or 0,
                "quality_consistency": region.quality_consistency_score or 0,
            },
        }

    @staticmethod
    def _score_elevation(elevation_min_m: float | None, elevation_max_m: float | None) -> float:
        if not elevation_min_m or not elevation_max_m:
            return 0.0
        avg_elevation = (elevation_min_m + elevation_max_m) / 2
        if 1200 <= avg_elevation <= 2000:
            return 30.0
        if 1000 <= avg_elevation < 1200 or 2000 < avg_elevation <= 2200:
            return 25.0
        if 800 <= avg_elevation < 1000 or 2200 < avg_elevation <= 2400:
            return 20.0
        return 10.0

    @staticmethod
    def _score_temperature(avg_temperature_c: float | None) -> float:
        if not avg_temperature_c:
            return 0.0
        if 18 <= avg_temperature_c <= 22:
            return 20.0
        if 16 <= avg_temperature_c < 18 or 22 < avg_temperature_c <= 24:
            return 15.0
        if 14 <= avg_temperature_c < 16 or 24 < avg_temperature_c <= 26:
            return 10.0
        return 5.0

    @staticmethod
    def _score_rainfall(rainfall_mm: float | None) -> float:
        if not rainfall_mm:
            return 0.0
        if 1500 <= rainfall_mm <= 2500:
            return 20.0
        if 1200 <= rainfall_mm < 1500 or 2500 < rainfall_mm <= 3000:
            return 15.0
        if 1000 <= rainfall_mm < 1200 or 3000 < rainfall_mm <= 3500:
            return 10.0
        return 5.0

    @staticmethod
    def _score_soil(soil_type: str | None) -> float:
        if not soil_type:
            return 0.0
        soil_lower = soil_type.lower()
        if any(term in soil_lower for term in ["volcanic", "loam", "rich"]):
            return 30.0
        if any(term in soil_lower for term in ["clay", "sandy loam"]):
            return 25.0
        if "sandy" in soil_lower:
            return 15.0
        return 20.0

    def calculate_growing_conditions_score(self, region: Region) -> float:
        """
        Calculate growing conditions score (0-100).

        Scoring algorithm:
        - Elevation (30 points): Optimal 1200-2000m
        - Climate (40 points): Temperature 18-22°C, Rainfall 1500-2500mm
        - Soil (30 points): Based on soil quality assessment

        Args:
            region: Region model instance

        Returns:
            Score from 0-100
        """
        score = 0.0
        score += self._score_elevation(region.elevation_min_m, region.elevation_max_m)
        score += self._score_temperature(region.avg_temperature_c)
        score += self._score_rainfall(region.rainfall_mm)
        score += self._score_soil(region.soil_type)
        return round(score, 2)

    def refresh_region_data(self, region_name: str) -> dict[str, Any]:
        """
        Refresh region data from external sources and update the database.

        Args:
            region_name: Name of the region

        Returns:
            Dictionary with refresh status and data sources
        """
        region = self._resolve_region(region_name)
        lookup_name = region.name if region else region_name

        # Fetch from external sources using canonical name when available
        jnc_data = fetch_jnc_data(lookup_name)
        minagri_data = fetch_minagri_data(lookup_name)
        weather_data = fetch_senamhi_weather(lookup_name)

        updated_fields = []

        if region and weather_data.get("available"):
            # Update weather-related fields
            weather_info = weather_data.get("data", {})
            if weather_info.get("current_temperature_c"):
                region.avg_temperature_c = weather_info["current_temperature_c"]
                updated_fields.append("avg_temperature_c")

            # Note: updated_at is automatically updated by SQLAlchemy's onupdate trigger

            self.db.commit()

        return {
            "region": lookup_name,
            "refreshed": True,
            "updated_fields": updated_fields,
            "sources": {
                "jnc": jnc_data,
                "minagri": minagri_data,
                "weather": weather_data,
            },
            "note": (
                f"Updated {len(updated_fields)} fields in database"
                if updated_fields
                else "No database updates (data unavailable or region not found)"
            ),
        }
