"""
Phase 2 Data Pipeline Orchestrator
Coordinates all 17 data sources through 9 provider modules
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
import json

logger = logging.getLogger(__name__)

class DataPipelineOrchestrator:
    """Orchestrates all Phase 2 data collection from 17 sources"""
    
    SOURCE_GROUPS = {
        "Market": ["coffee_prices", "fx_rates"],
        "Weather": ["weather", "agronomic"],
        "Shipping": ["shipping_data", "port_data"],
        "News": ["newsapi", "twitter_sentiment", "reddit_sentiment", "web_scraping"],
        "Macro": ["inei", "wits", "bcrp", "ico", "coffee_research"]
    }
    
    SOURCES = [
        # Gruppe A: Market (5)
        "Yahoo Finance",       # Coffee C Futures
        "ECB API",            # EUR Wechselkurse
        "OANDA FX",           # Zusätzliche Währungspaare
        "OpenMeteo",          # Wetter
        "NewsAPI",            # Marktintelligenz
        
        # Gruppe B: Weather (4)
        "RAIN4PE",            # Peru Niederschläge
        "Weatherbit",         # Bodenfeuchtigkeit
        "NASA GPM",           # Globale Niederschläge
        "SENAMHI",            # Peru Wetterdaten
        
        # Gruppe C: Sentiment (3)
        "Twitter API",        # Social Sentiment
        "Reddit API",         # Community Sentiment
        "Coffee Blogs",       # Web-Scraping
        
        # Gruppe D: Shipping (2)
        "MarineTraffic",      # Hafen-Datenverkehr
        "AIS Stream",         # Schiff-Tracking
        
        # Gruppe E: Macro (3)
        "INEI Peru",          # Nationale Statistiken
        "World Bank WITS",    # Handelsdaten
        "BCRP Peru",          # Makro-Indikatoren
        
        # Gruppe F: Coffee Industry (2)
        "ICO",                # International Coffee Org
        "Coffee Research"     # Qualitätsmetriken
    ]
    
    def __init__(self):
        self.status = "idle"
        self.last_run = None
        self.next_run = None
        self.collected_records = 0
        self.errors = []
        self.circuit_breakers = {source: {"status": "closed", "trips": 0} for source in self.SOURCES}
    
    async def run_full_pipeline(self) -> Dict:
        """Execute complete data collection from all 17 sources"""
        logger.info("Starting Phase 2 Full Pipeline")
        self.status = "running"
        self.last_run = datetime.utcnow()
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "running",
            "sources_attempted": len(self.SOURCES),
            "data_collected": {}
        }
        
        # Import all provider modules
        try:
            from app.providers import coffee_prices, fx_rates, weather, shipping_data
            from app.providers import news_market, peru_macro
        except ImportError as e:
            logger.error(f"Provider import error: {str(e)}")
            results["status"] = "error"
            return results
        
        # Collect from each source
        try:
            # Market Sources
            logger.info("Collecting market data...")
            coffee_price = coffee_prices.fetch_coffee_price() if hasattr(coffee_prices, 'fetch_coffee_price') else None
            results["data_collected"]["coffee_prices"] = coffee_price
            
            fx_data = fx_rates.fetch_fx_rate("EUR", "USD") if hasattr(fx_rates, 'fetch_fx_rate') else None
            results["data_collected"]["fx_rates"] = fx_data
            
            # Weather Sources
            logger.info("Collecting weather data...")
            weather_data = weather.WeatherProvider.fetch_all_weather()
            results["data_collected"]["weather"] = weather_data
            self.collected_records += len(weather_data) if weather_data else 0
            
            # Shipping Sources
            logger.info("Collecting shipping data...")
            vessel_data = shipping_data.ShippingProvider.fetch_vessel_tracking()
            port_data = shipping_data.ShippingProvider.fetch_port_status()
            results["data_collected"]["shipping"] = vessel_data
            results["data_collected"]["ports"] = port_data
            self.collected_records += len(vessel_data) if vessel_data else 0
            self.collected_records += len(port_data) if port_data else 0
            
            # News & Sentiment Sources
            logger.info("Collecting news and sentiment data...")
            intelligence = news_market.NewsProvider.fetch_all_intelligence()
            results["data_collected"]["intelligence"] = intelligence
            
            # Macro Sources
            logger.info("Collecting macro data...")
            macro_data = peru_macro.MacroProvider.fetch_all_macro_data()
            results["data_collected"]["macro"] = macro_data
            
        except Exception as e:
            logger.error(f"Pipeline execution error: {str(e)}")
            self.errors.append(str(e))
            results["status"] = "error_partial"
        
        results["status"] = "completed" if not self.errors else "completed_with_errors"
        results["records_collected"] = self.collected_records
        results["errors"] = self.errors
        
        self.status = "idle"
        return results
    
    def check_circuit_breaker(self, source: str) -> bool:
        """Check if source circuit breaker is open"""
        if source not in self.circuit_breakers:
            return True  # Source not tracked, allow
        
        return self.circuit_breakers[source]["status"] == "closed"
    
    def trip_circuit_breaker(self, source: str):
        """Trip circuit breaker for failing source"""
        if source in self.circuit_breakers:
            cb = self.circuit_breakers[source]
            cb["trips"] += 1
            if cb["trips"] >= 3:
                cb["status"] = "open"
                logger.warning(f"Circuit breaker OPEN for {source}")
    
    def reset_circuit_breaker(self, source: str):
        """Reset circuit breaker after recovery"""
        if source in self.circuit_breakers:
            cb = self.circuit_breakers[source]
            cb["status"] = "closed"
            cb["trips"] = 0
            logger.info(f"Circuit breaker RESET for {source}")
    
    def get_pipeline_status(self) -> Dict:
        """Get current pipeline status"""
        return {
            "status": self.status,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "total_sources": len(self.SOURCES),
            "records_collected_total": self.collected_records,
            "circuit_breakers": self.circuit_breakers,
            "error_count": len(self.errors),
            "timestamp": datetime.utcnow().isoformat()
        }


# Singleton instance
orchestrator = DataPipelineOrchestrator()


async def run_phase2_pipeline() -> Dict:
    """Run Phase 2 pipeline"""
    return await orchestrator.run_full_pipeline()


def get_pipeline_health() -> Dict:
    """Get health metrics for monitoring dashboard"""
    return orchestrator.get_pipeline_status()
