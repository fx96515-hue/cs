# Phase 1 Database Setup

PR721 Phase 1 was integrated conservatively.

## Included

- additive models in `apps/api/app/models/weather_agronomic.py`
- safe Alembic migration `0020_full_stack_data_models.py`

## New Additive Tables

- `weather_agronomic_data`
- `social_sentiment_data`
- `shipment_api_events`
- `ml_features_cache`
- `data_lineage_log`
- `source_health_metrics`

## Intentionally Excluded

- risky seed logic into existing core tables
- schema assumptions not present on current `main`
