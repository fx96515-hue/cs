from fastapi import APIRouter

from app.api.routes import discovery, health, rag_analyst
from app.domains.assistant.api import chat_routes as assistant
from app.domains.auth.api import routes as auth
from app.domains.auto_outreach.api import routes as auto_outreach
from app.domains.cooperatives.api import routes as cooperatives
from app.domains.cuppings.api import routes as cuppings
from app.domains.data_quality.api import routes as data_quality
from app.domains.deals.api import routes as deals
from app.domains.dedup.api import routes as dedup
from app.domains.enrich.api import routes as enrich
from app.domains.features.api import routes as features_dashboard
from app.domains.health.api import data_health_routes as data_health
from app.domains.kb.api import routes as kb
from app.domains.knowledge_graph.api import routes as knowledge_graph
from app.domains.logistics.api import routes as logistics
from app.domains.lots.api import routes as lots
from app.domains.margins.api import routes as margins
from app.domains.market.api import routes as market
from app.domains.ml_predictions.api import routes as ml_predictions
from app.domains.ml_training.api import routes as ml_routes
from app.domains.monitoring.api import routes as monitoring_dashboard
from app.domains.news.api import routes as news
from app.domains.ops.api import routes as ops_dashboard
from app.domains.outreach.api import routes as outreach
from app.domains.peru_sourcing.api import routes as peru_sourcing
from app.domains.pipeline.api import routes as pipeline_dashboard
from app.domains.price_quotes.api import routes as price_quotes
from app.domains.quality_alerts.api import routes as quality_alerts
from app.domains.regions.api import routes as regions
from app.domains.reports.api import routes as reports
from app.domains.roasters.api import routes as roasters
from app.domains.scheduler.api import routes as scheduler_dashboard
from app.domains.semantic_search.api import routes as semantic_search
from app.domains.sentiment.api import routes as sentiment
from app.domains.shipments.api import routes as shipments
from app.domains.sources.api import routes as sources
from app.domains.transport_events.api import routes as transport_events

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(
    cooperatives.router, prefix="/cooperatives", tags=["cooperatives"]
)
api_router.include_router(roasters.router, prefix="/roasters", tags=["roasters"])
api_router.include_router(discovery.router, prefix="/discovery", tags=["discovery"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(lots.router, prefix="/lots", tags=["lots"])
api_router.include_router(deals.router, prefix="/deals", tags=["deals"])
api_router.include_router(margins.router, prefix="/margins", tags=["margins"])
api_router.include_router(enrich.router, prefix="/enrich", tags=["enrich"])
api_router.include_router(dedup.router, prefix="/dedup", tags=["dedup"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(regions.router, prefix="/regions", tags=["regions"])
api_router.include_router(logistics.router, prefix="/logistics", tags=["logistics"])
api_router.include_router(outreach.router, prefix="/outreach", tags=["outreach"])
api_router.include_router(kb.router, prefix="/kb", tags=["kb"])
api_router.include_router(cuppings.router, prefix="/cuppings", tags=["cuppings"])
api_router.include_router(ml_predictions.router, prefix="/ml", tags=["ml"])
api_router.include_router(peru_sourcing.router, prefix="/peru", tags=["peru-sourcing"])
api_router.include_router(shipments.router, prefix="/shipments", tags=["shipments"])
api_router.include_router(
    transport_events.router, prefix="/transport-events", tags=["transport-events"]
)
api_router.include_router(
    price_quotes.router, prefix="/price-quotes", tags=["price-quotes"]
)
api_router.include_router(
    data_health.router, prefix="/data-health", tags=["data-health"]
)
api_router.include_router(
    quality_alerts.router, prefix="/alerts", tags=["quality-alerts"]
)
api_router.include_router(
    quality_alerts.anomalies_router, prefix="/anomalies", tags=["anomaly-detection"]
)
api_router.include_router(
    auto_outreach.router, prefix="/auto-outreach", tags=["auto-outreach"]
)
api_router.include_router(ops_dashboard.router, prefix="/ops", tags=["ops-dashboard"])
api_router.include_router(ml_routes.router, prefix="/ml/train", tags=["ml-training"])
api_router.include_router(semantic_search.router, tags=["semantic-search"])
api_router.include_router(rag_analyst.router, prefix="/analyst", tags=["rag-analyst"])
api_router.include_router(
    knowledge_graph.router, prefix="/graph", tags=["knowledge-graph"]
)
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
api_router.include_router(sentiment.router, prefix="/sentiment", tags=["sentiment"])
api_router.include_router(
    data_quality.router, prefix="/data-quality", tags=["data-quality"]
)
api_router.include_router(
    pipeline_dashboard.router, prefix="/pipeline", tags=["pipeline-dashboard"]
)
api_router.include_router(
    features_dashboard.router, prefix="/features", tags=["features-dashboard"]
)
api_router.include_router(
    scheduler_dashboard.router, prefix="/scheduler", tags=["scheduler-dashboard"]
)
api_router.include_router(
    monitoring_dashboard.router, prefix="/monitoring", tags=["monitoring-dashboard"]
)
