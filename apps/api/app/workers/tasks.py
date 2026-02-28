from __future__ import annotations

import structlog
from datetime import datetime, timezone

import redis
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.report import Report
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster
from app.services.reports import generate_daily_report
from app.services.discovery import seed_discovery
from app.services.enrichment import enrich_entity
from app.services.data_pipeline.orchestrator import DataPipelineOrchestrator
from app.services.data_pipeline.freshness import DataFreshnessMonitor
from app.workers.celery_app import celery

log = structlog.get_logger()


def _db() -> Session:
    return SessionLocal()


def _redis() -> redis.Redis:
    """Get Redis connection."""
    return redis.from_url(settings.REDIS_URL)


def _parse_date(value):
    from datetime import date, datetime

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError("Invalid date value")


@celery.task(name="app.workers.tasks.refresh_market")
def refresh_market():
    """Refresh market observations and generate a daily report.

    Enhanced with multi-source fallback and circuit breaker protection.
    """
    db = _db()
    redis_client = _redis()
    try:
        now = datetime.now(timezone.utc)

        # Use orchestrator for market data pipeline
        orchestrator = DataPipelineOrchestrator(db, redis_client)
        pipeline_result = orchestrator.run_market_pipeline()

        log.info(
            "market_refresh",
            status=pipeline_result["status"],
            duration_s=pipeline_result["duration_seconds"],
            errors=pipeline_result["errors"],
        )

        # Generate report
        md, payload = generate_daily_report(db)
        rep = Report(
            kind="daily",
            title=f"Tagesreport {now.date().isoformat()}",
            report_at=now,
            markdown=md,
            payload=payload,
        )
        db.add(rep)
        db.commit()
        db.refresh(rep)

        return {
            "status": pipeline_result["status"],
            "pipeline": pipeline_result,
            "report_id": rep.id,
        }
    finally:
        db.close()
        redis_client.close()


@celery.task(name="app.workers.tasks.refresh_news")
def refresh_news():
    """Refresh Market Radar news and ensure Peru region KB is seeded.

    Note: This task is kept for backward compatibility.
    For full intelligence pipeline, use refresh_intelligence instead.
    """
    db = _db()
    redis_client = _redis()
    try:
        orchestrator = DataPipelineOrchestrator(db, redis_client)
        result = orchestrator.run_intelligence_pipeline()
        log.info("news_refresh", **result)

        # Run sentiment analysis after news refresh when enabled
        if getattr(settings, "SENTIMENT_ENABLED", False):
            try:
                from app.services.sentiment import (
                    analyze_news_items,
                    aggregate_region_sentiment,
                )

                sentiment_result = analyze_news_items(db)
                aggregate_region_sentiment(db)
                log.info("sentiment_after_news_refresh", **sentiment_result)
            except Exception as e:
                log.warning("sentiment_after_news_error", error=str(e))

        return result
    finally:
        db.close()
        redis_client.close()


@celery.task(name="app.workers.tasks.refresh_intelligence")
def refresh_intelligence():
    """Refresh Peru intelligence + enrichment pipeline.

    Includes:
    - Peru weather data (OpenMeteo)
    - News refresh
    - Entity enrichment for stale entities
    - Sentiment analysis (when SENTIMENT_ENABLED)
    """
    db = _db()
    redis_client = _redis()
    try:
        orchestrator = DataPipelineOrchestrator(db, redis_client)
        result = orchestrator.run_intelligence_pipeline()
        log.info("intelligence_refresh", **result)

        # Run sentiment analysis after intelligence refresh when enabled
        if getattr(settings, "SENTIMENT_ENABLED", False):
            try:
                from app.services.sentiment import (
                    analyze_news_items,
                    aggregate_region_sentiment,
                )

                sentiment_result = analyze_news_items(db)
                aggregate_region_sentiment(db)
                log.info("sentiment_after_intel_refresh", **sentiment_result)
            except Exception as e:
                log.warning("sentiment_after_intel_error", error=str(e))

        return result
    finally:
        db.close()
        redis_client.close()


@celery.task(name="app.workers.tasks.auto_enrich_stale")
def auto_enrich_stale():
    """Auto-enrich entities that haven't been updated in KOOPS_STALE_DAYS.

    Finds the top 10 stalest cooperatives and roasters and enriches them.
    """
    db = _db()
    try:
        monitor = DataFreshnessMonitor(db)

        # Get stale cooperatives
        stale_coops = monitor.get_stale_entities(
            "cooperative", settings.KOOPS_STALE_DAYS
        )
        log.info("auto_enrich_stale_cooperatives", count=len(stale_coops))

        enriched_coops = 0
        for coop_id in stale_coops:
            try:
                coop = db.query(Cooperative).get(coop_id)
                if coop and coop.website:
                    enrich_entity(
                        db,
                        entity_type="cooperative",
                        entity_id=coop_id,
                        url=coop.website,
                        use_llm=True,
                    )
                    enriched_coops += 1
            except Exception as e:
                log.warning(
                    "auto_enrich_cooperative_failed",
                    coop_id=coop_id,
                    error=str(e),
                )

        # Get stale roasters
        stale_roasters = monitor.get_stale_entities(
            "roaster", settings.ROESTER_STALE_DAYS
        )
        log.info("auto_enrich_stale_roasters", count=len(stale_roasters))

        enriched_roasters = 0
        for roaster_id in stale_roasters:
            try:
                roaster = db.query(Roaster).get(roaster_id)
                if roaster and roaster.website:
                    enrich_entity(
                        db,
                        entity_type="roaster",
                        entity_id=roaster_id,
                        url=roaster.website,
                        use_llm=True,
                    )
                    enriched_roasters += 1
            except Exception as e:
                log.warning(
                    "auto_enrich_roaster_failed",
                    roaster_id=roaster_id,
                    error=str(e),
                )

        return {
            "status": "ok",
            "cooperatives_enriched": enriched_coops,
            "roasters_enriched": enriched_roasters,
            "total_enriched": enriched_coops + enriched_roasters,
        }
    finally:
        db.close()


@celery.task(name="app.workers.tasks.seed_discovery")
def seed_discovery_task(
    entity_type: str,
    max_entities: int = 100,
    dry_run: bool = False,
    country_filter: str | None = None,
):
    """Seed cooperatives/roasters via Perplexity discovery.

    Notes:
    - Requires PERPLEXITY_API_KEY.
    - Uses conservative upsert: fill empty fields, store evidence URLs.
    """
    db = _db()
    try:
        if entity_type == "both":
            a = seed_discovery(
                db,
                entity_type="cooperative",
                max_entities=max_entities,
                dry_run=dry_run,
                country_filter=country_filter,
            )
            b = seed_discovery(
                db,
                entity_type="roaster",
                max_entities=max_entities,
                dry_run=dry_run,
                country_filter=country_filter,
            )
            return {"cooperatives": a, "roasters": b}
        return seed_discovery(
            db,
            entity_type=entity_type,
            max_entities=max_entities,
            dry_run=dry_run,
            country_filter=country_filter,
        )
    finally:
        db.close()


@celery.task(name="app.workers.tasks.check_quality_alerts")
def check_quality_alerts(threshold: float = 5.0):
    """Check for quality score changes and create alerts.

    Args:
        threshold: Minimum score change to trigger alert (default: 5.0)
    """
    from app.services.quality_alerts import check_all_entities

    db = _db()
    try:
        result = check_all_entities(db, threshold=threshold)
        log.info("quality_alerts_check", **result)
        return result
    finally:
        db.close()


@celery.task(name="app.workers.tasks.run_anomaly_scan")
def run_anomaly_scan():
    """Daily anomaly scan: Isolation Forest for entity scores + Z-Score for prices.

    Skips execution when ANOMALY_DETECTION_ENABLED=false.
    """
    from app.core.config import settings

    if not settings.ANOMALY_DETECTION_ENABLED:
        log.info("anomaly_scan_skipped", reason="feature_flag_disabled")
        return {"status": "skipped", "reason": "ANOMALY_DETECTION_ENABLED=false"}

    from app.services.anomaly_detection import run_anomaly_scan as _run

    db = _db()
    try:
        result = _run(db)
        log.info("anomaly_scan_done", **result)
        return result
    finally:
        db.close()


@celery.task(name="app.workers.tasks.auto_outreach_follow_up")
def auto_outreach_follow_up(entity_type: str, days_threshold: int = 7):
    """Follow up on outreach campaigns for entities that haven't responded.

    Args:
        entity_type: 'cooperative' or 'roaster'
        days_threshold: Days since last contact to trigger follow-up
    """
    from app.services.auto_outreach import get_outreach_suggestions
    from app.models.entity_event import EntityEvent

    db = _db()
    try:
        # Get entities needing follow-up
        # This is a simplified implementation
        # In production, would query EntityEvents more sophisticatedly
        suggestions = get_outreach_suggestions(db, entity_type=entity_type, limit=10)

        follow_ups = []
        for suggestion in suggestions:
            # Create follow-up event
            db.add(
                EntityEvent(
                    entity_type=entity_type,
                    entity_id=suggestion["entity_id"],
                    event_type="outreach_follow_up",
                    payload={"reason": "automated_follow_up"},
                )
            )
            follow_ups.append(suggestion["entity_id"])

        db.commit()

        result = {
            "status": "ok",
            "entity_type": entity_type,
            "follow_ups_created": len(follow_ups),
            "entity_ids": follow_ups,
        }
        log.info("auto_outreach_follow_up", **result)
        return result
    finally:
        db.close()


@celery.task(name="app.workers.tasks.train_ml_model")
def train_ml_model(model_type: str):
    """Train ML model (freight or coffee price).

    Args:
        model_type: 'freight_cost' or 'coffee_price'
    """
    from app.services.ml.training_pipeline import train_freight_model, train_price_model

    db = _db()
    try:
        if model_type == "freight_cost":
            result = train_freight_model(db)
        elif model_type == "coffee_price":
            result = train_price_model(db)
        else:
            return {
                "status": "error",
                "message": f"Unknown model type: {model_type}",
            }

        log.info("ml_model_training", model_type=model_type, **result)
        return result
    except Exception as e:
        log.error("ml_model_training_failed", model_type=model_type, error=str(e))
        return {"status": "error", "model_type": model_type, "error": str(e)}
    finally:
        db.close()


@celery.task(
    name="app.workers.tasks.predict_freight_batch",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def predict_freight_batch(self, payloads: list[dict]):
    """Run batch freight cost predictions in the background."""
    import asyncio
    from app.services.ml.freight_prediction import FreightPredictionService

    db = _db()
    try:
        service = FreightPredictionService(db)
        results: list[dict | None] = []
        errors: list[dict] = []

        async def _run():
            for idx, item in enumerate(payloads):
                try:
                    result = await service.predict_freight_cost(
                        origin_port=item["origin_port"],
                        destination_port=item["destination_port"],
                        weight_kg=item["weight_kg"],
                        container_type=item["container_type"],
                        departure_date=_parse_date(item["departure_date"]),
                    )
                    results.append(result)
                except Exception as exc:
                    results.append(None)
                    errors.append({"index": idx, "error": str(exc)})

        asyncio.run(_run())
        return {"status": "ok", "results": results, "errors": errors}
    finally:
        db.close()


@celery.task(
    name="app.workers.tasks.predict_coffee_price_batch",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def predict_coffee_price_batch(self, payloads: list[dict]):
    """Run batch coffee price predictions in the background."""
    import asyncio
    from app.services.ml.price_prediction import CoffeePricePredictionService

    db = _db()
    try:
        service = CoffeePricePredictionService(db)
        results: list[dict | None] = []
        errors: list[dict] = []

        async def _run():
            for idx, item in enumerate(payloads):
                try:
                    result = await service.predict_coffee_price(
                        origin_country=item["origin_country"],
                        origin_region=item["origin_region"],
                        variety=item["variety"],
                        process_method=item["process_method"],
                        quality_grade=item["quality_grade"],
                        cupping_score=item["cupping_score"],
                        certifications=item.get("certifications") or [],
                        forecast_date=_parse_date(item["forecast_date"]),
                    )
                    results.append(result)
                except Exception as exc:
                    results.append(None)
                    errors.append({"index": idx, "error": str(exc)})

        asyncio.run(_run())
        return {"status": "ok", "results": results, "errors": errors}
    finally:
        db.close()


@celery.task(name="app.workers.tasks.generate_embeddings")
def generate_embeddings(entity_type: str | None = None, batch_size: int = 50):
    """Generate embeddings for all entities without embeddings.

    Args:
        entity_type: 'cooperative' or 'roaster' or None for both
        batch_size: Number of entities to process in one batch
    """
    import asyncio
    from app.services.embedding import EmbeddingService

    db = _db()
    try:
        service = EmbeddingService()

        if not service.is_available():
            log.warning(
                "embeddings_task_skipped",
                provider=service.provider_name,
                reason="embedding_provider_unavailable",
            )
            return {
                "status": "skipped",
                "reason": f"Embedding provider '{service.provider_name}' is not available",
            }

        async def process_entities(entity_cls, entity_name):
            # Get entities without embeddings
            entities = (
                db.query(entity_cls)
                .filter(entity_cls.embedding.is_(None))
                .limit(batch_size)
                .all()
            )

            if not entities:
                log.info(f"no_{entity_name}_without_embeddings")
                return 0

            # Generate texts for batch processing
            texts = [service.generate_entity_text(e) for e in entities]

            # Generate embeddings in batch
            embeddings = await service.generate_embeddings_batch(texts)

            # Update entities
            updated = 0
            for entity, embedding in zip(entities, embeddings):
                if embedding:
                    entity.embedding = embedding
                    updated += 1

            db.commit()
            log.info(
                f"{entity_name}_embeddings_generated",
                total=len(entities),
                updated=updated,
            )
            return updated

        # Process based on entity_type
        results = {}
        if entity_type in (None, "cooperative"):
            coop_count = asyncio.run(process_entities(Cooperative, "cooperative"))
            results["cooperatives"] = coop_count

        if entity_type in (None, "roaster"):
            roaster_count = asyncio.run(process_entities(Roaster, "roaster"))
            results["roasters"] = roaster_count

        return {
            "status": "ok",
            "updated": results,
        }
    except Exception as e:
        log.error("generate_embeddings_failed", error=str(e))
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery.task(name="app.workers.tasks.update_entity_embedding")
def update_entity_embedding(entity_type: str, entity_id: int):
    """Update embedding for a single entity.

    Args:
        entity_type: 'cooperative' or 'roaster'
        entity_id: Entity ID
    """
    import asyncio
    from app.services.embedding import EmbeddingService

    db = _db()
    try:
        service = EmbeddingService()

        if not service.is_available():
            log.warning(
                "embedding_update_skipped",
                provider=service.provider_name,
                reason="embedding_provider_unavailable",
            )
            return {
                "status": "skipped",
                "reason": f"Embedding provider '{service.provider_name}' is not available",
            }

        # Get entity
        entity: Cooperative | Roaster | None
        if entity_type == "cooperative":
            entity = db.query(Cooperative).filter(Cooperative.id == entity_id).first()
        elif entity_type == "roaster":
            entity = db.query(Roaster).filter(Roaster.id == entity_id).first()
        else:
            return {"status": "error", "message": "Invalid entity_type"}

        if not entity:
            return {"status": "error", "message": "Entity not found"}

        # Generate embedding
        async def generate():
            return await service.generate_entity_embedding(entity)

        embedding = asyncio.run(generate())

        if embedding:
            entity.embedding = embedding
            db.commit()
            log.info(
                "entity_embedding_updated",
                entity_type=entity_type,
                entity_id=entity_id,
            )
            return {"status": "ok", "entity_type": entity_type, "entity_id": entity_id}
        else:
            return {"status": "error", "message": "Embedding generation failed"}
    except Exception as e:
        log.error(
            "update_entity_embedding_failed",
            entity_type=entity_type,
            entity_id=entity_id,
            error=str(e),
        )
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery.task(name="app.workers.tasks.analyze_sentiment")
def analyze_sentiment():
    """Score unscored news items and aggregate region sentiment.

    Respects the SENTIMENT_ENABLED feature flag.
    """
    if not getattr(settings, "SENTIMENT_ENABLED", False):
        return {"status": "skipped", "reason": "SENTIMENT_ENABLED is false"}

    from app.services.sentiment import analyze_news_items, aggregate_region_sentiment

    db = _db()
    try:
        result = analyze_news_items(db)
        agg = aggregate_region_sentiment(db)
        log.info("analyze_sentiment_task", **result)
        return {
            "status": result["status"],
            "scored": result["scored"],
            "regions": agg.get("regions"),
        }
    except Exception as e:
        log.error("analyze_sentiment_failed", error=str(e))
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
