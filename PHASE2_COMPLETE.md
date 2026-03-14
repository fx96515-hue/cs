# Phase 2 Provider Integration

Integrated from PR721 in safe form:

- `apps/api/app/providers/weather.py`
- `apps/api/app/providers/shipping_data.py`
- `apps/api/app/providers/news_market.py`
- `apps/api/app/providers/peru_macro.py`
- `apps/api/app/services/data_pipeline/phase2_orchestrator.py`

## Design Choice

These modules act as provider catalogs and optional fetch layers. The hardened
existing orchestrator remains the ingest source of truth.
