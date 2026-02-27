"""
API routes for Peru sourcing intelligence.

Endpoints for region intelligence, cooperative sourcing analysis,
and data management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import require_role
from app.db.session import get_db
from app.models.region import Region
from app.schemas.peru_sourcing import (
    RegionIntelligenceResponse,
    RegionBasicResponse,
    SourcingAnalysisResponse,
    AnalyzeCooperativeRequest,
    RefreshRegionRequest,
)
from app.services.peru_sourcing_intel import PeruRegionIntelService
from app.services.cooperative_sourcing_analyzer import CooperativeSourcingAnalyzer
from app.services.seed_peru_regions import seed_peru_regions


router = APIRouter()


@router.get("/regions", response_model=list[RegionBasicResponse])
def list_peru_regions(
    db: Session = Depends(get_db), _=Depends(require_role("admin", "analyst", "viewer"))
):
    """
    List all Peru coffee regions with basic information.

    Returns summary data for all regions including production share and quality scores.
    """
    stmt = select(Region).where(Region.country == "Peru").order_by(Region.name.asc())
    regions = db.scalars(stmt).all()

    return [
        RegionBasicResponse(
            id=r.id,
            name=r.name,
            country=r.country,
            production_share_pct=r.production_share_pct,
            quality_consistency_score=r.quality_consistency_score,
        )
        for r in regions
    ]


@router.get(
    "/regions/{region_name}/intelligence", response_model=RegionIntelligenceResponse
)
def get_region_intelligence(
    region_name: str,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """
    Get comprehensive intelligence for a specific Peru region.

    Returns detailed information including:
    - Growing conditions and climate
    - Production data and quality profiles
    - Logistics and infrastructure
    - Risk assessments
    - Calculated scores
    """
    service = PeruRegionIntelService(db)
    intelligence = service.get_region_intelligence(region_name)

    if not intelligence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region '{region_name}' not found",
        )

    return intelligence


@router.get(
    "/cooperatives/{coop_id}/sourcing-analysis", response_model=SourcingAnalysisResponse
)
def get_cooperative_sourcing_analysis(
    coop_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """
    Get sourcing analysis for a cooperative (uses cached results if available).

    Returns comprehensive analysis including:
    - Supply capacity assessment
    - Export readiness evaluation
    - Communication quality metrics
    - Price benchmarking
    - Risk assessment
    - Overall recommendation

    For fresh analysis, use the POST /analyze endpoint.
    """
    analyzer = CooperativeSourcingAnalyzer(db)

    try:
        analysis = analyzer.analyze_for_sourcing(coop_id, force_refresh=False)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/cooperatives/{coop_id}/analyze", response_model=SourcingAnalysisResponse)
def analyze_cooperative_for_sourcing(
    coop_id: int,
    request: AnalyzeCooperativeRequest | None = None,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    """
    Perform fresh sourcing analysis for a cooperative.

    This endpoint always performs a fresh calculation, bypassing any cached results.
    The results are cached in the cooperative's sourcing_scores field.

    Calculates:
    - Supply capacity (30% weight)
    - Export readiness (20% weight)
    - Communication quality (10% weight)
    - Price competitiveness (15% weight)
    - Quality score (25% weight)
    - Risk assessment
    - Overall recommendation
    """
    analyzer = CooperativeSourcingAnalyzer(db)

    # Always force refresh on POST /analyze endpoint
    force_refresh = True if request is None else request.force_refresh

    try:
        analysis = analyzer.analyze_for_sourcing(coop_id, force_refresh=force_refresh)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/regions/refresh")
def refresh_region_data(
    request: RefreshRegionRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    """
    Refresh region data from external sources.

    Fetches latest data from:
    - Junta Nacional del Café (JNC)
    - Ministerio de Agricultura (MINAGRI)
    - SENAMHI weather service

    Note: Currently returns stub data as external integrations are pending.
    """
    service = PeruRegionIntelService(db)
    result = service.refresh_region_data(request.region_name)
    return result


@router.post("/regions/seed")
def seed_regions(db: Session = Depends(get_db), _=Depends(require_role("admin"))):
    """
    Seed database with Peru region data.

    Creates or updates 6 major Peru coffee regions:
    - Cajamarca (30% production)
    - Junín (20% production)
    - San Martín (18% production)
    - Cusco (15% production)
    - Amazonas (8% production)
    - Puno (5% production)

    Each region includes comprehensive data on production, quality, logistics, and risks.
    """
    result = seed_peru_regions(db)
    return result
