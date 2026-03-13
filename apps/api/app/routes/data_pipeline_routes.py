"""
Phase 2 Data Pipeline API Routes
Endpoints to trigger and monitor data collection
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data-pipeline", tags=["data-pipeline"])

# Import Phase 2 orchestrator
from app.services.data_pipeline.phase2_orchestrator import (
    run_phase2_pipeline,
    get_pipeline_health,
    orchestrator
)

# Import providers
from app.providers import (
    coffee_prices, fx_rates, weather, shipping_data,
    news_market, peru_macro
)


@router.post("/trigger-full-collection")
async def trigger_full_collection(background_tasks: BackgroundTasks) -> Dict:
    """
    Trigger full data collection from all 17 sources
    
    Returns:
        Dict with collection status and record counts
    """
    try:
        # Run in background
        background_tasks.add_task(run_phase2_pipeline)
        
        return {
            "status": "collection_started",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Data collection from 17 sources initiated",
            "sources_total": len(orchestrator.SOURCES)
        }
    except Exception as e:
        logger.error(f"Collection trigger error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def pipeline_health() -> Dict:
    """
    Get pipeline health status
    
    Returns:
        Dict with status of all sources and circuit breakers
    """
    return get_pipeline_health()


@router.get("/sources")
async def list_sources() -> Dict:
    """
    List all 17 configured data sources
    
    Returns:
        Grouped list of sources by category
    """
    return {
        "total_sources": len(orchestrator.SOURCES),
        "source_groups": orchestrator.SOURCE_GROUPS,
        "all_sources": orchestrator.SOURCES,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/source-status/{source_name}")
async def source_status(source_name: str) -> Dict:
    """
    Get status for specific data source
    
    Args:
        source_name: Name of source to check
    
    Returns:
        Dict with source health, circuit breaker status, last success
    """
    if source_name not in orchestrator.SOURCES:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_name}")
    
    cb = orchestrator.circuit_breakers.get(source_name, {})
    
    return {
        "source_name": source_name,
        "circuit_breaker_status": cb.get("status", "unknown"),
        "circuit_breaker_trips": cb.get("trips", 0),
        "healthy": cb.get("status") == "closed",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/collections/latest")
async def latest_collection() -> Dict:
    """
    Get latest collection results
    
    Returns:
        Dict with timestamps and record counts per source
    """
    status = get_pipeline_health()
    
    return {
        "last_run": status.get("last_run"),
        "records_collected_total": status.get("records_collected_total"),
        "sources_tracked": status.get("total_sources"),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/coffee-prices/latest")
async def get_latest_coffee_price() -> Dict:
    """Fetch latest Coffee C Futures price"""
    try:
        from app.providers.coffee_prices import fetch_coffee_price
        price = fetch_coffee_price()
        
        if not price:
            raise HTTPException(status_code=503, detail="Unable to fetch coffee price")
        
        return {
            "source": price.source_name,
            "price_usd_per_lb": price.price_usd_per_lb,
            "observed_at": price.observed_at.isoformat(),
            "metadata": price.metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Coffee price fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fx-rates/{base}/{quote}")
async def get_fx_rate(base: str, quote: str) -> Dict:
    """Fetch FX rate for currency pair"""
    try:
        from app.providers.fx_rates import fetch_fx_rate
        rate = fetch_fx_rate(base.upper(), quote.upper())
        
        if not rate:
            raise HTTPException(status_code=503, detail=f"Unable to fetch {base}/{quote}")
        
        return {
            "base": rate.base,
            "quote": rate.quote,
            "rate": rate.rate,
            "source": rate.source_name,
            "observed_at": rate.observed_at.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"FX rate fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weather/peru-regions")
async def get_peru_weather() -> Dict:
    """Fetch weather for all Peru coffee regions"""
    try:
        weather_data = weather.WeatherProvider.fetch_all_weather()
        
        return {
            "regions_count": len(weather_data) if weather_data else 0,
            "data": weather_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Peru weather fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shipping/vessels")
async def get_vessel_tracking() -> Dict:
    """Fetch vessel tracking data"""
    try:
        vessels = shipping_data.ShippingProvider.fetch_vessel_tracking()
        
        return {
            "vessels_count": len(vessels) if vessels else 0,
            "data": vessels,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Vessel tracking fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shipping/ports")
async def get_port_status() -> Dict:
    """Fetch port congestion data"""
    try:
        ports = shipping_data.ShippingProvider.fetch_port_status()
        
        return {
            "ports_count": len(ports) if ports else 0,
            "data": ports,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Port status fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intelligence/news")
async def get_coffee_news() -> Dict:
    """Fetch coffee market news"""
    try:
        news = news_market.NewsAPIProvider.fetch_coffee_news()
        
        return {
            "articles_count": len(news) if news else 0,
            "data": news[:10],  # Return top 10
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"News fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intelligence/sentiment/twitter")
async def get_twitter_sentiment() -> Dict:
    """Fetch Twitter sentiment"""
    try:
        sentiment = news_market.TwitterSentimentProvider.fetch_sentiment()
        
        return {
            "keywords_count": len(sentiment) if sentiment else 0,
            "data": sentiment,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Twitter sentiment fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/macro/peru-production")
async def get_peru_coffee_production() -> Dict:
    """Fetch Peru coffee production statistics"""
    try:
        production = peru_macro.INEIProvider.fetch_coffee_production()
        
        return {
            "data": production,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Peru production fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/macro/trade-exports")
async def get_trade_data() -> Dict:
    """Fetch Peru coffee trade data"""
    try:
        exports = peru_macro.WorldBankWITSProvider.fetch_peru_coffee_exports()
        
        return {
            "data": exports,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Trade data fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ico/market-report")
async def get_ico_report() -> Dict:
    """Fetch ICO global coffee market report"""
    try:
        report = peru_macro.ICOProvider.fetch_global_market_report()
        
        return {
            "data": report,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"ICO report fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
