"""
Pydantic schemas for Peru sourcing intelligence API.

Response models for region intelligence, cooperative sourcing analysis,
and related endpoints.
"""

from pydantic import BaseModel, Field
from typing import Any


# Region schemas
class RegionElevationRange(BaseModel):
    min_m: float | None = None
    max_m: float | None = None


class RegionClimate(BaseModel):
    avg_temperature_c: float | None = None
    rainfall_mm: float | None = None
    humidity_pct: float | None = None


class RegionProduction(BaseModel):
    volume_kg: float | None = None
    share_pct: float | None = None
    harvest_months: str | None = None


class RegionQuality(BaseModel):
    typical_varieties: str | None = None
    typical_processing: str | None = None
    profile: str | None = None
    consistency_score: float | None = None


class RegionLogistics(BaseModel):
    main_port: str | None = None
    transport_time_hours: float | None = None
    cost_per_kg: float | None = None
    infrastructure_score: float | None = None


class RegionRisks(BaseModel):
    weather: str | None = None
    political: str | None = None
    logistics: str | None = None


class RegionScores(BaseModel):
    growing_conditions: float
    infrastructure: float
    quality_consistency: float


class RegionIntelligenceResponse(BaseModel):
    name: str
    country: str
    description: str | None = None
    elevation_range: RegionElevationRange
    climate: RegionClimate
    soil_type: str | None = None
    production: RegionProduction
    quality: RegionQuality
    logistics: RegionLogistics
    risks: RegionRisks
    scores: RegionScores


class RegionBasicResponse(BaseModel):
    id: int
    name: str
    country: str
    production_share_pct: float | None = None
    quality_consistency_score: float | None = None


# Sourcing analysis schemas
class SupplyCapacityResponse(BaseModel):
    score: float
    max_score: int = 100
    breakdown: dict[str, Any]
    assessment: str


class ExportReadinessResponse(BaseModel):
    score: float
    max_score: int = 100
    breakdown: dict[str, Any]
    assessment: str


class CommunicationQualityResponse(BaseModel):
    score: float
    max_score: int = 100
    breakdown: dict[str, Any]
    assessment: str


class PriceBenchmarkResponse(BaseModel):
    competitiveness_score: float
    coop_price: float | None = None
    benchmark_price: float | None = None
    benchmark_source: str | None = None
    price_difference_pct: float | None = None
    assessment: str


class RiskAssessmentResponse(BaseModel):
    total_risk_score: float
    max_risk_score: int = 100
    breakdown: dict[str, Any]
    assessment: str


class RecommendationResponse(BaseModel):
    level: str
    reasoning: str
    total_score: float
    risk_score: float


class SourcingScoresResponse(BaseModel):
    supply_capacity: float
    quality: float
    export_readiness: float
    price_competitiveness: float
    communication: float
    total: float


class SourcingAnalysisResponse(BaseModel):
    cooperative_id: int
    cooperative_name: str
    region: str | None = None
    analyzed_at: str
    total_score: float
    supply_capacity: SupplyCapacityResponse
    export_readiness: ExportReadinessResponse
    communication_quality: CommunicationQualityResponse
    price_benchmark: PriceBenchmarkResponse
    risk_assessment: RiskAssessmentResponse
    scores: SourcingScoresResponse
    recommendation: RecommendationResponse


# Request schemas
class AnalyzeCooperativeRequest(BaseModel):
    force_refresh: bool = Field(
        default=False, description="Force fresh analysis, bypassing cache"
    )


class RefreshRegionRequest(BaseModel):
    region_name: str = Field(..., description="Name of the region to refresh")
