# Data Governance and Canonical Data Model

This document captures the governance layer added for enterprise-grade data control
and the canonical model alignment for the CoffeeStudio platform.

## Governance Layer (Persistent)
- Audit trail: `audit_logs` captures CRUD actions, actor details, and payloads.
- Entity versioning: `entity_versions` stores immutable snapshots per entity/version.
- Data quality flags: `data_quality_flags` tracks completeness/consistency issues.
- Soft delete: core entities now support `deleted_at` instead of hard deletes.

## Canonical Model Alignment
- Regions: `cooperatives.region_id` (FK to `regions`) for normalized geography.
- Shipments: `shipment_lots` join table for many-to-many shipment-lot relationships.
- Prices: `coffee_price_history.market_key` aligns with `market_observations.key`.

## Operational Notes
- Soft deletes are applied to: `cooperatives`, `roasters`, `lots`, `shipments`, `regions`.
- API list/get endpoints filter `deleted_at IS NULL` by default.
- Audit logs and entity versions are persisted on create/update/delete flows.

## Follow-up (Recommended)
- Backfill `region_id` from existing `cooperatives.region` strings.
- Enforce `shipment_lots` as the source of truth and deprecate `shipments.lot_id`.
- Add data quality rules to auto-create flags during ingestion.

## Backfill Scripts
Run from `apps/api` with the backend environment configured:

```bash
python scripts/backfill_regions.py
python scripts/backfill_shipment_lots.py
python scripts/backfill_market_key.py
python scripts/recompute_data_quality.py
```
