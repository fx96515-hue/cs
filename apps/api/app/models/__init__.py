"""SQLAlchemy models for CoffeeStudio API."""

# Core entities
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster
from app.models.lot import Lot
from app.models.deal import Deal
from app.models.shipment import Shipment
from app.models.shipment_lot import ShipmentLot
from app.models.user import User

# Market & pricing
from app.models.market import MarketObservation
from app.models.price_quote import PriceQuote
from app.models.margin import Margin

# ML Training data
from app.models.freight_history import FreightHistory
from app.models.coffee_price_history import CoffeePriceHistory
from app.models.ml_model import MLModel

# Quality & cupping
from app.models.cupping import Cupping
from app.models.quality_alert import QualityAlert
from app.models.data_quality_flag import DataQualityFlag

# Intelligence & research
from app.models.news_item import NewsItem
from app.models.sentiment_score import SentimentScore
from app.models.knowledge_doc import KnowledgeDoc
from app.models.web_extract import WebExtract
from app.models.source import Source

# Regions
from app.models.region import Region
from app.models.peru_region import PeruRegion

# Tracking & audit
from app.models.audit_log import AuditLog
from app.models.entity_version import EntityVersion
from app.models.entity_event import EntityEvent
from app.models.entity_alias import EntityAlias
from app.models.evidence import EntityEvidence
from app.models.transport_event import TransportEvent
from app.models.report import Report

# Full Stack Data Models (Phase 1)
from app.models.weather_agronomic import (
    WeatherAgronomicData,
    SocialSentimentData,
    ShipmentApiEvent,
    MLFeaturesCache,
    DataLineageLog,
    SourceHealthMetrics,
)

__all__ = [
    # Core entities
    "Cooperative",
    "Roaster",
    "Lot",
    "Deal",
    "Shipment",
    "ShipmentLot",
    "User",
    # Market & pricing
    "MarketObservation",
    "PriceQuote",
    "Margin",
    # ML Training data
    "FreightHistory",
    "CoffeePriceHistory",
    "MLModel",
    # Quality & cupping
    "Cupping",
    "QualityAlert",
    "DataQualityFlag",
    # Intelligence & research
    "NewsItem",
    "SentimentScore",
    "KnowledgeDoc",
    "WebExtract",
    "Source",
    # Regions
    "Region",
    "PeruRegion",
    # Tracking & audit
    "AuditLog",
    "EntityVersion",
    "EntityEvent",
    "EntityAlias",
    "EntityEvidence",
    "TransportEvent",
    "Report",
    # Full Stack Data Models (Phase 1)
    "WeatherAgronomicData",
    "SocialSentimentData",
    "ShipmentApiEvent",
    "MLFeaturesCache",
    "DataLineageLog",
    "SourceHealthMetrics",
]
