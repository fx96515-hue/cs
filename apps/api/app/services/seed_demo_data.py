"""
Seed demo data for cooperatives, roasters, and market observations.

This module provides idempotent demo data seeding for when PERPLEXITY_API_KEY
is not available or for initial testing purposes.
"""

from datetime import datetime, timezone
from typing import Any, cast
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.cooperative import Cooperative
from app.models.roaster import Roaster
from app.models.market import MarketObservation


# Demo cooperatives data - realistic Peru coffee cooperatives
DEMO_COOPERATIVES = [
    {
        "name": "Cooperativa Agraria Cafetalera Frontera San Ignacio",
        "region": "Cajamarca",
        "altitude_m": 1600,
        "varieties": "Caturra, Bourbon, Typica",
        "certifications": "Organic, Fair Trade, Rainforest Alliance",
        "contact_email": "info@cafrontera.com",
        "website": "https://www.cafrontera.com",
        "status": "active",
        "quality_score": 88.5,
        "reliability_score": 92.0,
        "economics_score": 85.0,
        "meta": {
            "country": "Peru",
            "country_code": "PE",
            "members_count": 1200,
            "annual_production_kg": 800000,
        },
    },
    {
        "name": "CENFROCAFE - Central Fronteriza del Norte de Cafetaleros",
        "region": "Cajamarca",
        "altitude_m": 1700,
        "varieties": "Caturra, Catimor, Bourbon",
        "certifications": "Organic, Fair Trade, UTZ",
        "contact_email": "exportaciones@cenfrocafe.com.pe",
        "website": "https://www.cenfrocafe.com.pe",
        "status": "active",
        "quality_score": 86.0,
        "reliability_score": 89.0,
        "economics_score": 87.5,
        "meta": {
            "country": "Peru",
            "country_code": "PE",
            "members_count": 2000,
            "annual_production_kg": 1200000,
        },
    },
    {
        "name": "Sol y Café",
        "region": "Cusco",
        "altitude_m": 1800,
        "varieties": "Bourbon, Typica, Caturra",
        "certifications": "Organic, Fair Trade",
        "contact_email": "info@solycafe.com",
        "website": "https://www.solycafe.com",
        "status": "active",
        "quality_score": 90.0,
        "reliability_score": 91.0,
        "economics_score": 83.0,
        "meta": {
            "country": "Peru",
            "country_code": "PE",
            "members_count": 650,
            "annual_production_kg": 450000,
        },
    },
    {
        "name": "Cooperativa Agraria Norandino",
        "region": "Cajamarca",
        "altitude_m": 1500,
        "varieties": "Caturra, Bourbon, Pache",
        "certifications": "Organic, Fair Trade, Rainforest Alliance, UTZ",
        "contact_email": "norandino@norandino.com.pe",
        "website": "https://www.norandino.com.pe",
        "status": "active",
        "quality_score": 87.5,
        "reliability_score": 94.0,
        "economics_score": 90.0,
        "meta": {
            "country": "Peru",
            "country_code": "PE",
            "members_count": 7000,
            "annual_production_kg": 3500000,
        },
    },
    {
        "name": "CAC Pangoa",
        "region": "Junín",
        "altitude_m": 1400,
        "varieties": "Caturra, Catimor, Bourbon",
        "certifications": "Organic, Fair Trade",
        "contact_email": "exportaciones@cacpangoa.com.pe",
        "website": "https://www.cacpangoa.com.pe",
        "status": "active",
        "quality_score": 84.0,
        "reliability_score": 87.0,
        "economics_score": 86.0,
        "meta": {
            "country": "Peru",
            "country_code": "PE",
            "members_count": 900,
            "annual_production_kg": 600000,
        },
    },
    {
        "name": "Cooperativa Agraria Cafetalera Huadquiña",
        "region": "Cusco",
        "altitude_m": 1650,
        "varieties": "Typica, Bourbon, Caturra",
        "certifications": "Organic, Fair Trade, Rainforest Alliance",
        "contact_email": "info@huadquina.org",
        "website": "https://www.huadquina.org",
        "status": "active",
        "quality_score": 89.0,
        "reliability_score": 88.0,
        "economics_score": 84.0,
        "meta": {
            "country": "Peru",
            "country_code": "PE",
            "members_count": 550,
            "annual_production_kg": 380000,
        },
    },
    {
        "name": "Cooperativa de Servicios Múltiples Valle de Incahuasi",
        "region": "San Martín",
        "altitude_m": 1300,
        "varieties": "Caturra, Catimor",
        "certifications": "Organic, Fair Trade",
        "contact_email": "incahuasi@gmail.com",
        "website": None,
        "status": "active",
        "quality_score": 82.0,
        "reliability_score": 85.0,
        "economics_score": 80.0,
        "meta": {
            "country": "Peru",
            "country_code": "PE",
            "members_count": 400,
            "annual_production_kg": 250000,
        },
    },
    {
        "name": "CECOCAFEN - Central de Cooperativas Agrarias Cafetaleras",
        "region": "Amazonas",
        "altitude_m": 1550,
        "varieties": "Caturra, Bourbon, Catimor",
        "certifications": "Organic, Fair Trade",
        "contact_email": "cecocafen@cecocafen.com.pe",
        "website": "https://www.cecocafen.com.pe",
        "status": "active",
        "quality_score": 85.5,
        "reliability_score": 86.0,
        "economics_score": 82.5,
        "meta": {
            "country": "Peru",
            "country_code": "PE",
            "members_count": 1500,
            "annual_production_kg": 900000,
        },
    },
    # --- Colombia (CO) ---
    {
        "name": "Cooperativa de Caficultores de Antioquia",
        "region": "Antioquia",
        "altitude_m": 1750,
        "varieties": "Castillo, Caturra, Colombia",
        "certifications": "FNC Registered, Organic, Fair Trade",
        "contact_email": "info@coopantioquia.com.co",
        "website": "https://www.coopantioquia.com.co",
        "status": "active",
        "quality_score": 87.0,
        "reliability_score": 91.0,
        "economics_score": 86.0,
        "meta": {
            "country": "Colombia",
            "country_code": "CO",
            "members_count": 3500,
            "annual_production_kg": 2100000,
        },
    },
    {
        "name": "Asociación de Productores de Café de Huila",
        "region": "Huila",
        "altitude_m": 1900,
        "varieties": "Caturra, Castillo, Geisha",
        "certifications": "Organic, Fair Trade, Rainforest Alliance",
        "contact_email": "exportaciones@cafehuila.com.co",
        "website": "https://www.cafehuila.com.co",
        "status": "active",
        "quality_score": 91.5,
        "reliability_score": 89.0,
        "economics_score": 88.0,
        "meta": {
            "country": "Colombia",
            "country_code": "CO",
            "members_count": 1200,
            "annual_production_kg": 750000,
        },
    },
    {
        "name": "Cooperativa Departamental de Caficultores de Nariño",
        "region": "Nariño",
        "altitude_m": 2100,
        "varieties": "Caturra, Colombia, Typica",
        "certifications": "Organic, Fair Trade",
        "contact_email": "info@coopcafenariño.com.co",
        "website": None,
        "status": "active",
        "quality_score": 92.0,
        "reliability_score": 88.0,
        "economics_score": 85.0,
        "meta": {
            "country": "Colombia",
            "country_code": "CO",
            "members_count": 800,
            "annual_production_kg": 480000,
        },
    },
    # --- Ethiopia (ET) ---
    {
        "name": "Yirgacheffe Coffee Farmers Cooperative Union",
        "region": "Gedeo Zone, SNNP",
        "altitude_m": 1900,
        "varieties": "Heirloom Ethiopian, Typica",
        "certifications": "Organic, Fair Trade, ECX Registered",
        "contact_email": "info@ycfcu.org",
        "website": "https://www.ycfcu.org",
        "status": "active",
        "quality_score": 93.0,
        "reliability_score": 87.0,
        "economics_score": 82.0,
        "meta": {
            "country": "Ethiopia",
            "country_code": "ET",
            "members_count": 45000,
            "annual_production_kg": 8000000,
        },
    },
    {
        "name": "Sidama Coffee Farmers Cooperative Union",
        "region": "Sidama",
        "altitude_m": 2000,
        "varieties": "Heirloom Ethiopian",
        "certifications": "Organic, Fair Trade, ECX Registered",
        "contact_email": "sidamacoffee@ethionet.et",
        "website": "https://www.sidamacoffee.com",
        "status": "active",
        "quality_score": 91.0,
        "reliability_score": 86.0,
        "economics_score": 80.0,
        "meta": {
            "country": "Ethiopia",
            "country_code": "ET",
            "members_count": 72000,
            "annual_production_kg": 12000000,
        },
    },
    {
        "name": "Oromia Coffee Farmers Cooperative Union",
        "region": "Oromia",
        "altitude_m": 1850,
        "varieties": "Heirloom Ethiopian, Jimma",
        "certifications": "Organic, Fair Trade",
        "contact_email": "info@oromiacoffeeunion.org",
        "website": "https://www.oromiacoffeeunion.org",
        "status": "active",
        "quality_score": 89.0,
        "reliability_score": 85.0,
        "economics_score": 81.0,
        "meta": {
            "country": "Ethiopia",
            "country_code": "ET",
            "members_count": 200000,
            "annual_production_kg": 35000000,
        },
    },
    # --- Brazil (BR) ---
    {
        "name": "Cooxupé – Cooperativa Regional de Cafeicultores em Guaxupé",
        "region": "Minas Gerais",
        "altitude_m": 900,
        "varieties": "Catuaí, Mundo Novo, Bourbon",
        "certifications": "CECAFÉ Member, UTZ, Rainforest Alliance",
        "contact_email": "exportacao@cooxupe.com.br",
        "website": "https://www.cooxupe.com.br",
        "status": "active",
        "quality_score": 85.0,
        "reliability_score": 95.0,
        "economics_score": 92.0,
        "meta": {
            "country": "Brazil",
            "country_code": "BR",
            # Real-world production is higher (~180M kg), but this is reduced for demo/analytics stability.
            "members_count": 14000,
            "annual_production_kg": 75000000,
        },
    },
    {
        "name": "Cooperativa dos Cafeicultores da Zona de Varginha",
        "region": "Sul de Minas",
        "altitude_m": 1050,
        "varieties": "Catuaí, Bourbon, Icatu",
        "certifications": "CECAFÉ Member, Organic, Fair Trade",
        "contact_email": "info@coopagrisa.com.br",
        "website": "https://www.coopagrisa.com.br",
        "status": "active",
        "quality_score": 87.5,
        "reliability_score": 92.0,
        "economics_score": 89.0,
        "meta": {
            "country": "Brazil",
            "country_code": "BR",
            "members_count": 5000,
            "annual_production_kg": 60000000,
        },
    },
    {
        "name": "Cooperativa Agropecuária de Poços de Caldas",
        "region": "Cerrado Mineiro",
        "altitude_m": 1100,
        "varieties": "Mundo Novo, Catuaí, Bourbon Amarelo",
        "certifications": "CECAFÉ Member, Denomination of Origin",
        "contact_email": "exportacao@coopagrosa.com.br",
        "website": "https://www.coopagrosa.com.br",
        "status": "active",
        "quality_score": 86.0,
        "reliability_score": 90.0,
        "economics_score": 88.0,
        "meta": {
            "country": "Brazil",
            "country_code": "BR",
            "members_count": 3200,
            "annual_production_kg": 42000000,
        },
    },
]

# Demo roasters data - realistic German coffee roasters
DEMO_ROASTERS = [
    {
        "name": "Kaffeerösterei Speicherstadt",
        "city": "Hamburg",
        "website": "https://www.speicherstadt-kaffee.de",
        "contact_email": "kontakt@speicherstadt-kaffee.de",
        "peru_focus": True,
        "specialty_focus": True,
        "price_position": "premium",
        "status": "active",
        "total_score": 85.0,
        "meta": {
            "country": "DE",
            "founded_year": 1999,
        },
    },
    {
        "name": "The Barn Berlin",
        "city": "Berlin",
        "website": "https://thebarn.de",
        "contact_email": "hello@thebarn.de",
        "peru_focus": False,
        "specialty_focus": True,
        "price_position": "premium",
        "status": "active",
        "total_score": 92.0,
        "meta": {
            "country": "DE",
            "founded_year": 2010,
        },
    },
    {
        "name": "Hoppenworth & Ploch",
        "city": "Frankfurt",
        "website": "https://www.hoppenworth-ploch.de",
        "contact_email": "info@hoppenworth-ploch.de",
        "peru_focus": False,
        "specialty_focus": True,
        "price_position": "mid",
        "status": "active",
        "total_score": 78.0,
        "meta": {
            "country": "DE",
            "founded_year": 2011,
        },
    },
    {
        "name": "Mahlefitz Kaffeerösterei",
        "city": "München",
        "website": "https://www.mahlefitz.de",
        "contact_email": "info@mahlefitz.de",
        "peru_focus": True,
        "specialty_focus": True,
        "price_position": "premium",
        "status": "active",
        "total_score": 88.0,
        "meta": {
            "country": "DE",
            "founded_year": 2015,
        },
    },
    {
        "name": "Five Elephant",
        "city": "Berlin",
        "website": "https://www.fiveelephant.com",
        "contact_email": "hello@fiveelephant.com",
        "peru_focus": False,
        "specialty_focus": True,
        "price_position": "premium",
        "status": "active",
        "total_score": 90.0,
        "meta": {
            "country": "DE",
            "founded_year": 2010,
        },
    },
    {
        "name": "Bonanza Coffee",
        "city": "Berlin",
        "website": "https://www.bonanzacoffee.de",
        "contact_email": "info@bonanzacoffee.de",
        "peru_focus": False,
        "specialty_focus": True,
        "price_position": "premium",
        "status": "active",
        "total_score": 91.0,
        "meta": {
            "country": "DE",
            "founded_year": 2006,
        },
    },
    {
        "name": "Elephants & Butterflies Coffee",
        "city": "Stuttgart",
        "website": "https://www.elephants-butterflies.de",
        "contact_email": "info@elephants-butterflies.de",
        "peru_focus": True,
        "specialty_focus": True,
        "price_position": "mid",
        "status": "active",
        "total_score": 82.0,
        "meta": {
            "country": "DE",
            "founded_year": 2018,
        },
    },
    {
        "name": "Quijote Kaffee",
        "city": "Hamburg",
        "website": "https://www.quijote-kaffee.de",
        "contact_email": "info@quijote-kaffee.de",
        "peru_focus": True,
        "specialty_focus": True,
        "price_position": "mid",
        "status": "active",
        "total_score": 80.0,
        "meta": {
            "country": "DE",
            "founded_year": 1998,
        },
    },
]

# Demo market observations - reference prices
DEMO_MARKET_OBSERVATIONS = [
    {
        "key": "COFFEE_C:USD_LB",
        "value": 3.50,
        "unit": "lb",
        "currency": "USD",
        "meta": {
            "source": "Demo/Reference",
            "description": "ICE Coffee C Futures reference price",
        },
    },
    {
        "key": "EUR_USD",
        "value": 1.08,
        "unit": None,
        "currency": None,
        "meta": {
            "source": "Demo/Reference",
            "description": "EUR/USD exchange rate reference",
        },
    },
]


def seed_demo_cooperatives(db: Session) -> dict[str, Any]:
    """
    Seed demo cooperatives if table is empty.

    Args:
        db: Database session

    Returns:
        Dictionary with operation results
    """
    # Check if cooperatives table is empty
    count = db.query(Cooperative).count()
    if count > 0:
        return {
            "status": "skipped",
            "reason": "cooperatives table not empty",
            "existing_count": count,
        }

    created = 0
    for coop_data in DEMO_COOPERATIVES:
        coop = Cooperative(**coop_data)
        db.add(coop)
        created += 1

    db.commit()

    return {
        "status": "success",
        "created": created,
        "total": len(DEMO_COOPERATIVES),
    }


def seed_demo_roasters(db: Session) -> dict[str, Any]:
    """
    Seed demo roasters if table is empty.

    Args:
        db: Database session

    Returns:
        Dictionary with operation results
    """
    # Check if roasters table is empty
    count = db.query(Roaster).count()
    if count > 0:
        return {
            "status": "skipped",
            "reason": "roasters table not empty",
            "existing_count": count,
        }

    created = 0
    for roaster_data in DEMO_ROASTERS:
        roaster = Roaster(**roaster_data)
        db.add(roaster)
        created += 1

    db.commit()

    return {
        "status": "success",
        "created": created,
        "total": len(DEMO_ROASTERS),
    }


def seed_demo_market_data(db: Session) -> dict[str, Any]:
    """
    Seed demo market observations if they don't exist.

    Args:
        db: Database session

    Returns:
        Dictionary with operation results
    """
    created = 0
    updated = 0
    now = datetime.now(timezone.utc)

    for obs_data in DEMO_MARKET_OBSERVATIONS:
        # Check if observation with this key already exists
        stmt = select(MarketObservation).where(MarketObservation.key == obs_data["key"])
        existing = db.scalar(stmt)

        if existing:
            # Update if data is older than 24 hours
            age_hours = (now - existing.observed_at).total_seconds() / 3600
            if age_hours > 24:
                existing.value = cast(float, obs_data["value"])
                existing.observed_at = now
                meta_value = obs_data.get("meta")
                if meta_value:
                    existing.meta = cast(dict, meta_value)
                updated += 1
        else:
            # Create new observation
            obs = MarketObservation(
                key=obs_data["key"],
                value=obs_data["value"],
                unit=obs_data.get("unit"),
                currency=obs_data.get("currency"),
                observed_at=now,
                meta=obs_data.get("meta"),
            )
            db.add(obs)
            created += 1

    db.commit()

    return {
        "status": "success",
        "created": created,
        "updated": updated,
        "total": len(DEMO_MARKET_OBSERVATIONS),
    }


def seed_all_demo_data(db: Session) -> dict[str, Any]:
    """
    Seed all demo data (cooperatives, roasters, market observations).

    Args:
        db: Database session

    Returns:
        Dictionary with combined operation results
    """
    coops_result = seed_demo_cooperatives(db)
    roasters_result = seed_demo_roasters(db)
    market_result = seed_demo_market_data(db)

    return {
        "cooperatives": coops_result,
        "roasters": roasters_result,
        "market": market_result,
    }
