"""Data pipeline orchestrator.

Coordinates all data collection operations with proper sequencing,
error handling, and circuit breaker integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import redis
import structlog
from sqlalchemy.orm import Session

from app.core.config import settings
from app.providers.coffee_prices import fetch_coffee_price
from app.providers.fx_rates import fetch_fx_rate
from app.providers.peru_intel import fetch_openmeteo_weather
from app.services.data_pipeline.circuit_breaker import CircuitBreaker
from app.services.market_ingest import upsert_market_observation
from app.services.news import refresh_news as refresh_news_service
from app.services.peru_regions import seed_default_regions

log = structlog.get_logger()


@dataclass
class PipelineResult:
    """Result from pipeline execution."""

    status: str  # "success", "partial", "failed"
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    operations: dict
    errors: list[str]


class DataPipelineOrchestrator:
    """Enterprise-grade data collection orchestrator."""

    def __init__(self, db: Session, redis_client: redis.Redis):
        """Initialize orchestrator.

        Args:
            db: Database session
            redis_client: Redis connection for circuit breakers
        """
        self.db = db
        self.redis = redis_client

        # Initialize circuit breakers for each provider
        threshold = getattr(settings, "DATA_PIPELINE_CIRCUIT_BREAKER_THRESHOLD", 3)
        timeout = getattr(settings, "DATA_PIPELINE_CIRCUIT_BREAKER_TIMEOUT_S", 300)

        self.breakers = {
            "fx_rates": CircuitBreaker(
                redis_client,
                "fx_rates",
                failure_threshold=threshold,
                cooldown_seconds=timeout,
            ),
            "coffee_prices": CircuitBreaker(
                redis_client,
                "coffee_prices",
                failure_threshold=threshold,
                cooldown_seconds=timeout,
            ),
            "peru_weather": CircuitBreaker(
                redis_client,
                "peru_weather",
                failure_threshold=threshold,
                cooldown_seconds=timeout,
            ),
            "peru_intel": CircuitBreaker(
                redis_client,
                "peru_intel",
                failure_threshold=threshold,
                cooldown_seconds=timeout,
            ),
            "news": CircuitBreaker(
                redis_client,
                "news",
                failure_threshold=threshold,
                cooldown_seconds=timeout,
            ),
        }

    def _fetch_fx_with_breaker(self) -> Optional[dict]:
        """Fetch FX rates with circuit breaker protection."""
        breaker = self.breakers["fx_rates"]
        if not breaker.can_attempt():
            return None

        try:
            rate = fetch_fx_rate("USD", "EUR")
            if rate:
                obs = upsert_market_observation(
                    self.db,
                    key="FX:USD_EUR",
                    value=rate.rate,
                    unit=None,
                    currency=None,
                    observed_at=rate.observed_at,
                    source_name=rate.source_name,
                    source_url=rate.source_url,
                    raw_text=rate.raw_data,
                    meta={"base": rate.base, "quote": rate.quote},
                )
                breaker.record_success()
                log.info(
                    "fx_rate_ingested",
                    key=obs.key,
                    rate=rate.rate,
                    source=rate.source_name,
                )
                return {"success": True, "source": rate.source_name}
            else:
                breaker.record_failure()
                return None
        except Exception as e:
            breaker.record_failure()
            log.error("fx_rate_fetch_error", error=str(e), exc_info=True)
            return None

    def _fetch_coffee_with_breaker(self) -> Optional[dict]:
        """Fetch coffee prices with circuit breaker protection."""
        breaker = self.breakers["coffee_prices"]
        if not breaker.can_attempt():
            return None

        try:
            quote = fetch_coffee_price()
            if quote:
                obs = upsert_market_observation(
                    self.db,
                    key="COFFEE_C:USD_LB",
                    value=quote.price_usd_per_lb,
                    unit="lb",
                    currency="USD",
                    observed_at=quote.observed_at,
                    source_name=quote.source_name,
                    source_url=quote.source_url,
                    raw_text=quote.raw_data,
                    meta=quote.metadata,
                )
                breaker.record_success()
                log.info(
                    "coffee_price_ingested",
                    key=obs.key,
                    price=quote.price_usd_per_lb,
                    source=quote.source_name,
                )
                return {"success": True, "source": quote.source_name}
            else:
                breaker.record_failure()
                return None
        except Exception as e:
            breaker.record_failure()
            log.error("coffee_price_fetch_error", error=str(e), exc_info=True)
            return None

    def _fetch_peru_weather_with_breaker(self) -> dict:
        """Fetch Peru weather data with circuit breaker protection."""
        breaker = self.breakers["peru_weather"]
        if not breaker.can_attempt():
            return {"success": False, "regions": []}

        regions = [
            "Cajamarca",
            "Junín",
            "San Martín",
            "Cusco",
            "Amazonas",
            "Puno",
        ]
        ingested = []
        errors = []

        for region in regions:
            try:
                weather = fetch_openmeteo_weather(region)
                if weather:
                    key = f"WEATHER:PERU_{region.upper().replace(' ', '_')}"
                    upsert_market_observation(
                        self.db,
                        key=key,
                        value=weather.current_temp_c,
                        unit="celsius",
                        currency=None,
                        observed_at=weather.observed_at,
                        source_name=weather.source_name,
                        source_url=weather.source_url,
                        raw_text=weather.raw_data,
                        meta={
                            "region": region,
                            "temp_max": weather.temp_max_c,
                            "temp_min": weather.temp_min_c,
                            "precipitation": weather.precipitation_mm,
                        },
                    )
                    ingested.append(region)
                    log.info(
                        "peru_weather_ingested",
                        region=region,
                        temp=weather.current_temp_c,
                    )
                else:
                    errors.append(f"{region}: No data")
            except Exception as e:
                errors.append(f"{region}: {str(e)}")
                log.warning(
                    "peru_weather_fetch_error",
                    region=region,
                    error=str(e),
                )

        if ingested:
            breaker.record_success()
            return {
                "success": True,
                "regions": ingested,
                "errors": errors,
            }
        else:
            breaker.record_failure()
            return {"success": False, "regions": [], "errors": errors}

    def run_market_pipeline(self) -> dict:
        """Run market data pipeline (FX + coffee prices).

        Returns:
            Dictionary with results and status
        """
        log.info("market_pipeline_start")
        started_at = datetime.now(timezone.utc)

        results: dict[str, dict | None] = {"fx_rates": None, "coffee_prices": None}
        errors = []

        # FX rates (needed for price conversions)
        fx_result = self._fetch_fx_with_breaker()
        results["fx_rates"] = fx_result
        if not fx_result:
            errors.append("FX rates fetch failed or circuit open")

        # Coffee prices
        coffee_result = self._fetch_coffee_with_breaker()
        results["coffee_prices"] = coffee_result
        if not coffee_result:
            errors.append("Coffee prices fetch failed or circuit open")

        completed_at = datetime.now(timezone.utc)
        duration = (completed_at - started_at).total_seconds()

        status = (
            "success"
            if results["fx_rates"] and results["coffee_prices"]
            else "partial"
            if any(results.values())
            else "failed"
        )

        log.info(
            "market_pipeline_complete",
            status=status,
            duration_s=duration,
            errors=errors,
        )

        return {
            "status": status,
            "duration_seconds": round(duration, 2),
            "results": results,
            "errors": errors,
        }

    def run_intelligence_pipeline(self) -> dict:
        """Run intelligence pipeline (Peru weather + news).

        Returns:
            Dictionary with results and status
        """
        log.info("intelligence_pipeline_start")
        started_at = datetime.now(timezone.utc)

        results: dict[str, dict | None] = {"peru_weather": None, "news": None}
        errors = []

        # Seed Peru regions (idempotent)
        try:
            seed_default_regions(self.db)
        except Exception as e:
            log.warning("regions_seed_error", error=str(e))

        # Peru weather data
        weather_result = self._fetch_peru_weather_with_breaker()
        results["peru_weather"] = weather_result
        if not weather_result.get("success"):
            errors.append("Peru weather fetch failed or circuit open")

        # News refresh
        breaker = self.breakers["news"]
        if breaker.can_attempt():
            try:
                news_result = refresh_news_service(
                    self.db, topic="peru coffee", country="PE", max_items=25
                )
                results["news"] = news_result
                breaker.record_success()
                log.info("news_refresh_complete", **news_result)
            except Exception as e:
                breaker.record_failure()
                errors.append(f"News refresh failed: {str(e)}")
                log.error("news_refresh_error", error=str(e), exc_info=True)
        else:
            errors.append("News refresh circuit open")

        completed_at = datetime.now(timezone.utc)
        duration = (completed_at - started_at).total_seconds()

        status = (
            "success"
            if results["peru_weather"] and results["news"]
            else "partial"
            if any(results.values())
            else "failed"
        )

        log.info(
            "intelligence_pipeline_complete",
            status=status,
            duration_s=duration,
            errors=errors,
        )

        return {
            "status": status,
            "duration_seconds": round(duration, 2),
            "results": results,
            "errors": errors,
        }

    def run_full_pipeline(self) -> PipelineResult:
        """Run complete data pipeline.

        Executes in order:
        1. FX rates (needed for conversions)
        2. Coffee prices (needs FX)
        3. Peru weather
        4. News
        5. Scoring recomputation (if market data updated)

        Returns:
            PipelineResult with complete status
        """
        log.info("full_pipeline_start")
        started_at = datetime.now(timezone.utc)

        operations = {}
        errors = []

        # Market data
        market_result = self.run_market_pipeline()
        operations["market"] = market_result
        errors.extend(market_result.get("errors", []))

        # Intelligence data
        intel_result = self.run_intelligence_pipeline()
        operations["intelligence"] = intel_result
        errors.extend(intel_result.get("errors", []))

        # Recompute scores if market data updated
        if market_result.get("status") in ["success", "partial"]:
            try:
                from app.models.cooperative import Cooperative
                from app.services.scoring import (
                    recompute_and_persist_cooperative,
                )

                updated = 0
                for coop in self.db.query(Cooperative).all():
                    recompute_and_persist_cooperative(self.db, coop)
                    updated += 1

                operations["scoring"] = {
                    "success": True,
                    "cooperatives_updated": updated,
                }
                log.info("scoring_recompute_complete", updated=updated)
            except Exception as e:
                errors.append(f"Scoring recompute failed: {str(e)}")
                log.error("scoring_recompute_error", error=str(e), exc_info=True)

        completed_at = datetime.now(timezone.utc)
        duration = (completed_at - started_at).total_seconds()

        # Determine overall status
        if not errors:
            status = "success"
        elif operations:
            status = "partial"
        else:
            status = "failed"

        log.info(
            "full_pipeline_complete",
            status=status,
            duration_s=duration,
            error_count=len(errors),
        )

        return PipelineResult(
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=round(duration, 2),
            operations=operations,
            errors=errors,
        )

    def get_circuit_breaker_status(self) -> dict:
        """Get status of all circuit breakers.

        Returns:
            Dictionary with status of each circuit breaker
        """
        return {name: breaker.get_status() for name, breaker in self.breakers.items()}
