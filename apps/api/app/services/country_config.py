"""
Country configuration system for multi-country coffee sourcing expansion.

Supports onboarding of new origin countries with identical pipeline:
- Colombia (CO) – data source: FNC (Federación Nacional de Cafeteros)
- Ethiopia (ET) – data source: ECX (Ethiopian Commodity Exchange)
- Brazil (BR)   – data source: CECAFÉ (Conselho dos Exportadores de Café do Brasil)
- Peru (PE)     – existing default

Feature flag: set env var MULTI_COUNTRY_ENABLED=true to activate multi-country mode.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feature flag
# ---------------------------------------------------------------------------

MULTI_COUNTRY_ENABLED: bool = (
    os.getenv("MULTI_COUNTRY_ENABLED", "false").lower() in {"1", "true", "yes"}
)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HarvestCalendar:
    """Typical main and fly crop harvest windows (month numbers, 1-12).

    Note: When main_crop_end < main_crop_start, the harvest spans a year
    boundary (e.g. Oct=10 to Feb=2 means Oct–Feb across the calendar turn).
    Helper ``wraps_year`` indicates this case.
    """

    main_crop_start: int
    main_crop_end: int
    fly_crop_start: Optional[int] = None
    fly_crop_end: Optional[int] = None
    notes: str = ""

    @property
    def wraps_year(self) -> bool:
        """True when the main harvest window crosses a year boundary."""
        return self.main_crop_end < self.main_crop_start


@dataclass(frozen=True)
class DataSourceConfig:
    """External data source for a country."""

    name: str
    url: str
    kind: str = "api"  # api | web | manual
    reliability: float = 0.7
    description: str = ""


@dataclass(frozen=True)
class CountryConfig:
    """Full configuration for a coffee-origin country."""

    code: str                             # ISO-3166-1 alpha-2
    name: str                             # display name
    currency: str                         # ISO-4217 currency code
    currency_symbol: str
    flag_emoji: str
    data_source: DataSourceConfig
    harvest_calendar: HarvestCalendar
    discovery_cooperative_queries: List[str] = field(default_factory=list)
    discovery_roaster_queries: List[str] = field(default_factory=list)
    ml_country_feature: str = ""          # encoded label for ML models
    default_port: str = ""


# ---------------------------------------------------------------------------
# Country definitions
# ---------------------------------------------------------------------------

COUNTRY_CONFIGS: Dict[str, CountryConfig] = {
    "PE": CountryConfig(
        code="PE",
        name="Peru",
        currency="PEN",
        currency_symbol="S/",
        flag_emoji="🇵🇪",
        data_source=DataSourceConfig(
            name="PROMPERÚ",
            url="https://www.promperu.gob.pe/",
            kind="web",
            reliability=0.75,
            description="Peruvian export promotion agency",
        ),
        harvest_calendar=HarvestCalendar(
            main_crop_start=4,
            main_crop_end=9,
            notes="Main harvest April–September; varies by altitude",
        ),
        discovery_cooperative_queries=[
            "Peru coffee cooperative exporter list",
            "cooperativa cafetalera peru exportadora",
            "cooperativa cafe peru fairtrade organic",
            "central de cooperativas café Perú exportación",
            "Peru coffee cooperative Cajamarca",
            "Peru coffee cooperative Junin Satipo",
            "Peru coffee cooperative Puno Sandia",
            "Peru coffee cooperative San Martin Moyobamba",
            "Peru coffee cooperative Amazonas Chachapoyas",
            "Peru coffee cooperative Cusco Quillabamba",
            "cooperativa cafe peru cupping score specialty",
            "Peru specialty coffee producer exporter FOB price",
            "cooperativa agraria cafetalera peru organic fair trade export",
        ],
        discovery_roaster_queries=[
            "specialty coffee roaster Germany",
            "Kaffeerösterei Deutschland specialty direct trade",
            "Third Wave coffee roastery Deutschland",
            "Rösterei Berlin specialty coffee",
            "Rösterei München specialty coffee",
            "Rösterei Hamburg specialty coffee",
            "Rösterei Köln Düsseldorf specialty coffee",
            "Rösterei Stuttgart Frankfurt specialty coffee",
            "Rösterei Leipzig Dresden specialty coffee",
            "German specialty roaster Peru single origin",
            "Kaffeerösterei direct trade Peru Deutschland",
            "best specialty coffee roasters Germany 2024 2025",
        ],
        ml_country_feature="PE",
        default_port="Callao",
    ),
    "CO": CountryConfig(
        code="CO",
        name="Colombia",
        currency="COP",
        currency_symbol="COP$",
        flag_emoji="🇨🇴",
        data_source=DataSourceConfig(
            name="FNC",
            url="https://federaciondecafeteros.org/",
            kind="api",
            reliability=0.85,
            description="Federación Nacional de Cafeteros de Colombia",
        ),
        harvest_calendar=HarvestCalendar(
            main_crop_start=10,
            main_crop_end=2,
            fly_crop_start=4,
            fly_crop_end=6,
            notes="Main mitaca Oct–Feb; fly crop (traviesa) Apr–Jun; two harvests/year in many regions",
        ),
        discovery_cooperative_queries=[
            "Colombia coffee cooperative exporter FNC",
            "cooperativa cafetera Colombia exportadora",
            "Colombia specialty coffee cooperative Huila Nariño",
            "Colombia coffee cooperative Antioquia Cauca",
            "Colombia coffee cooperative fair trade organic certified",
            "Colombian coffee producer exporter FOB price specialty",
            "cooperativa cafe Colombia cupping score",
            "Colombia coffee cooperative direct trade exporter 2024",
        ],
        discovery_roaster_queries=[
            "specialty coffee roaster Germany Colombia single origin",
            "Kaffeerösterei Deutschland Colombia direct trade",
            "German specialty roaster Colombia coffee",
            "best Colombian coffee roasters Europe 2024 2025",
        ],
        ml_country_feature="CO",
        default_port="Buenaventura",
    ),
    "ET": CountryConfig(
        code="ET",
        name="Ethiopia",
        currency="ETB",
        currency_symbol="Br",
        flag_emoji="🇪🇹",
        data_source=DataSourceConfig(
            name="ECX",
            url="https://www.ecx.com.et/",
            kind="api",
            reliability=0.80,
            description="Ethiopian Commodity Exchange",
        ),
        harvest_calendar=HarvestCalendar(
            main_crop_start=10,
            main_crop_end=1,
            notes="Harvest October–January; drying and processing extend to March",
        ),
        discovery_cooperative_queries=[
            "Ethiopia coffee cooperative exporter ECX",
            "Ethiopian coffee washing station cooperative Yirgacheffe",
            "Ethiopia specialty coffee cooperative Sidama Guji",
            "Ethiopian coffee cooperative Kaffa Jimma exporter",
            "Ethiopia coffee cooperative organic fair trade certified",
            "Ethiopian specialty coffee producer direct trade exporter 2024",
            "Ethiopia coffee cooperative cupping score natural washed",
        ],
        discovery_roaster_queries=[
            "specialty coffee roaster Germany Ethiopia single origin",
            "Kaffeerösterei Deutschland Äthiopien direct trade",
            "German specialty roaster Ethiopian coffee Yirgacheffe",
            "best Ethiopian coffee roasters Europe 2024 2025",
        ],
        ml_country_feature="ET",
        default_port="Djibouti",
    ),
    "BR": CountryConfig(
        code="BR",
        name="Brazil",
        currency="BRL",
        currency_symbol="R$",
        flag_emoji="🇧🇷",
        data_source=DataSourceConfig(
            name="CECAFÉ",
            url="https://www.cecafe.com.br/",
            kind="web",
            reliability=0.82,
            description="Conselho dos Exportadores de Café do Brasil",
        ),
        harvest_calendar=HarvestCalendar(
            main_crop_start=5,
            main_crop_end=9,
            notes="Main harvest May–September; biennial production cycle",
        ),
        discovery_cooperative_queries=[
            "Brazil coffee cooperative exporter CECAFÉ",
            "cooperativa cafeeira Brasil exportadora specialty",
            "Brazil specialty coffee cooperative Minas Gerais",
            "Brazilian coffee cooperative São Paulo Espírito Santo",
            "Brazil coffee cooperative fair trade organic certified",
            "Brazilian specialty coffee producer exporter FOB 2024",
            "cooperativa cafe Brasil cupping score specialty",
        ],
        discovery_roaster_queries=[
            "specialty coffee roaster Germany Brazil single origin",
            "Kaffeerösterei Deutschland Brasilien direct trade",
            "German specialty roaster Brazilian coffee",
            "best Brazilian coffee roasters Europe 2024 2025",
        ],
        ml_country_feature="BR",
        default_port="Santos",
    ),
}

# Ordered list of all supported countries
SUPPORTED_COUNTRIES: List[str] = list(COUNTRY_CONFIGS.keys())


def get_country_config(code: str) -> Optional[CountryConfig]:
    """Return CountryConfig for the given ISO-2 code, or None if not found.

    Logs a warning when an unknown code is requested so callers can detect
    configuration gaps during development and operations.
    """
    result = COUNTRY_CONFIGS.get(code.upper())
    if result is None:
        log.warning("get_country_config: unknown country code %r", code)
    return result


def get_active_countries() -> List[CountryConfig]:
    """Return list of active country configs respecting the feature flag."""
    if MULTI_COUNTRY_ENABLED:
        return list(COUNTRY_CONFIGS.values())
    # Default: Peru only
    return [COUNTRY_CONFIGS["PE"]]
