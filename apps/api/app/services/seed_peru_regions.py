"""
Seed data for Peru coffee regions.

Comprehensive data for 6 major Peru coffee producing regions with production stats,
quality profiles, logistics information, and risk assessments.
"""

from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.region import Region


# Comprehensive seed data for Peru regions
PERU_REGIONS_DATA: list[dict[str, Any]] = [
    {
        "name": "Cajamarca",
        "country": "Peru",
        "description": "Northern Peru's largest coffee producing region, known for clean, sweet profiles and strong cooperative infrastructure.",
        "elevation_min_m": 1200,
        "elevation_max_m": 2100,
        "avg_temperature_c": 19.5,
        "rainfall_mm": 1800,
        "humidity_pct": 75,
        "soil_type": "Volcanic loam, rich in organic matter",
        "production_volume_kg": 75000000,  # 75,000 tons
        "production_share_pct": 30.0,
        "harvest_months": "April-September",
        "typical_varieties": "Bourbon, Caturra, Typica, Catimor",
        "typical_processing": "Washed (primary), Honey, Natural",
        "quality_profile": "Clean, sweet, balanced acidity, notes of chocolate, caramel, citrus. Consistent quality.",
        "main_port": "Callao",
        "transport_time_hours": 14.0,
        "logistics_cost_per_kg": 0.32,
        "infrastructure_score": 84.0,
        "weather_risk": "medium",
        "political_risk": "low",
        "logistics_risk": "low",
        "quality_consistency_score": 84.0,
    },
    {
        "name": "Junín",
        "country": "Peru",
        "description": "Central Peru region (Chanchamayo, Satipo) with excellent logistics and growing specialty focus.",
        "elevation_min_m": 1200,
        "elevation_max_m": 1800,
        "avg_temperature_c": 20.0,
        "rainfall_mm": 2000,
        "humidity_pct": 78,
        "soil_type": "Clay loam with good drainage",
        "production_volume_kg": 50000000,  # 50,000 tons
        "production_share_pct": 20.0,
        "harvest_months": "May-September",
        "typical_varieties": "Caturra, Catuaí, Typica, Bourbon",
        "typical_processing": "Washed, Honey, experimental fermentation",
        "quality_profile": "Bright acidity, medium body, fruity notes, floral undertones. Good consistency.",
        "main_port": "Callao",
        "transport_time_hours": 8.0,  # Best logistics
        "logistics_cost_per_kg": 0.28,  # Lower cost due to proximity
        "infrastructure_score": 88.0,  # Best infrastructure
        "weather_risk": "medium",
        "political_risk": "low",
        "logistics_risk": "low",
        "quality_consistency_score": 83.0,
    },
    {
        "name": "San Martín",
        "country": "Peru",
        "description": "Northern Amazon foothills, growing organic production with higher humidity challenges.",
        "elevation_min_m": 900,
        "elevation_max_m": 1700,
        "avg_temperature_c": 22.0,
        "rainfall_mm": 2500,
        "humidity_pct": 85,  # High humidity
        "soil_type": "Sandy loam, moderate fertility",
        "production_volume_kg": 45000000,  # 45,000 tons
        "production_share_pct": 18.0,
        "harvest_months": "April-August",
        "typical_varieties": "Caturra, Catuaí, Bourbon, Catimor",
        "typical_processing": "Washed, Natural (increasing)",
        "quality_profile": "Full body, low to medium acidity, nutty, chocolate notes. Variable quality due to drying challenges.",
        "main_port": "Callao",
        "transport_time_hours": 18.0,
        "logistics_cost_per_kg": 0.38,
        "infrastructure_score": 75.0,
        "weather_risk": "high",  # High humidity challenges
        "political_risk": "low",
        "logistics_risk": "medium",
        "quality_consistency_score": 81.0,
    },
    {
        "name": "Cusco",
        "country": "Peru",
        "description": "Southeastern Peru (La Convención valley), high altitude specialty coffees with complex profiles.",
        "elevation_min_m": 1400,
        "elevation_max_m": 2200,
        "avg_temperature_c": 18.0,
        "rainfall_mm": 1600,
        "humidity_pct": 70,
        "soil_type": "Volcanic, rich organic content",
        "production_volume_kg": 37500000,  # 37,500 tons
        "production_share_pct": 15.0,
        "harvest_months": "April-September",
        "typical_varieties": "Typica, Bourbon, Caturra, Catimor",
        "typical_processing": "Washed, Honey",
        "quality_profile": "Complex, bright acidity, floral, fruity, wine-like notes. Exceptional quality potential.",
        "main_port": "Callao",
        "transport_time_hours": 24.0,  # Longer due to mountain roads
        "logistics_cost_per_kg": 0.42,  # Higher cost
        "infrastructure_score": 78.0,
        "weather_risk": "medium",
        "political_risk": "low",
        "logistics_risk": "high",  # Mountain terrain challenges
        "quality_consistency_score": 86.0,
    },
    {
        "name": "Amazonas",
        "country": "Peru",
        "description": "Northern Peru, mountainous zones producing small lots with distinct clarity and brightness.",
        "elevation_min_m": 1200,
        "elevation_max_m": 2100,
        "avg_temperature_c": 19.0,
        "rainfall_mm": 1900,
        "humidity_pct": 80,
        "soil_type": "Clay loam, volcanic influence",
        "production_volume_kg": 20000000,  # 20,000 tons
        "production_share_pct": 8.0,
        "harvest_months": "May-September",
        "typical_varieties": "Caturra, Bourbon, Typica, Catuaí",
        "typical_processing": "Washed (dominant)",
        "quality_profile": "Clean, bright acidity, citrus, stone fruit, floral notes. High quality micro-lots.",
        "main_port": "Callao",
        "transport_time_hours": 20.0,
        "logistics_cost_per_kg": 0.40,
        "infrastructure_score": 76.0,
        "weather_risk": "medium",
        "political_risk": "low",
        "logistics_risk": "medium",
        "quality_consistency_score": 85.0,
    },
    {
        "name": "Puno",
        "country": "Peru",
        "description": "Southern Peru near Lake Titicaca and Bolivia border, very high altitude with distinctive floral profiles.",
        "elevation_min_m": 1500,
        "elevation_max_m": 2300,
        "avg_temperature_c": 17.0,
        "rainfall_mm": 1400,
        "humidity_pct": 65,
        "soil_type": "Volcanic, well-drained",
        "production_volume_kg": 12500000,  # 12,500 tons
        "production_share_pct": 5.0,
        "harvest_months": "May-September",
        "typical_varieties": "Bourbon, Typica, Caturra, Catuaí",
        "typical_processing": "Washed, Natural",
        "quality_profile": "Sweet, floral, delicate, complex. Distinctive high-altitude characteristics.",
        "main_port": "Callao",
        "transport_time_hours": 26.0,  # Longest distance
        "logistics_cost_per_kg": 0.45,  # Highest cost
        "infrastructure_score": 72.0,
        "weather_risk": "medium",
        "political_risk": "low",
        "logistics_risk": "high",  # Long distance and altitude
        "quality_consistency_score": 87.0,
    },
]


def seed_peru_regions(db: Session) -> dict[str, Any]:
    """
    Seed database with comprehensive Peru region data.

    Creates or updates 6 major Peru coffee regions with complete production,
    quality, logistics, and risk information.

    Args:
        db: Database session

    Returns:
        Dictionary with operation results
    """
    created = 0
    updated = 0

    for region_data in PERU_REGIONS_DATA:
        # Check if region exists
        stmt = select(Region).where(
            Region.name == region_data["name"], Region.country == region_data["country"]
        )
        region = db.scalar(stmt)

        if region:
            # Update existing region
            for key, value in region_data.items():
                if hasattr(region, key):
                    setattr(region, key, value)
            updated += 1
        else:
            # Create new region
            region = Region(**region_data)
            db.add(region)
            created += 1

    db.commit()

    return {
        "status": "success",
        "created": created,
        "updated": updated,
        "total_regions": len(PERU_REGIONS_DATA),
        "regions": [r["name"] for r in PERU_REGIONS_DATA],
    }


def get_region_summary() -> list[dict[str, Any]]:
    """
    Get summary information for all Peru regions.

    Returns:
        List of region summaries with key metrics
    """
    summaries = []
    for region in PERU_REGIONS_DATA:
        summaries.append(
            {
                "name": region["name"],
                "production_share": region["production_share_pct"],
                "elevation_range": f"{region['elevation_min_m']}-{region['elevation_max_m']}m",
                "quality_score": region["quality_consistency_score"],
                "infrastructure_score": region["infrastructure_score"],
                "logistics_risk": region["logistics_risk"],
            }
        )
    return summaries
