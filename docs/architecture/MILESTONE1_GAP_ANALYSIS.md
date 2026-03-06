Milestone 1 Gap Analysis (Target: Core Data Platform)
Date: 2026-02-28

Scope
Milestone 1 baseline requirements:
- Domain model for cooperatives, roasters, lots, shipments, transport, prices, quality data, and general lot/cooperative data
- Migrations in place for core entities
- CRUD APIs with filter/sort/pagination
- RBAC for admin/analyst/viewer
- Provenance (source, evidence, timestamps)
- Data quality flags and resolution workflow
- Basic UI for list/detail views

Current Coverage Summary
Status: Complete = present and usable, Partial = present with gaps, Missing = not implemented

- Cooperatives, Roasters, Lots: Complete
  Evidence: apps/api/app/models/cooperative.py, roaster.py, lot.py; routes in apps/api/app/api/routes
- Shipments: Partial
  Evidence: apps/api/app/models/shipment.py, shipment_lot.py; routes in apps/api/app/api/routes/shipments.py
  Gap: Date fields stored as strings; ambiguous single-lot vs many-lot modeling
- Transport: Partial
  Evidence: shipment tracking_events JSON in shipment.py
  Gap: No normalized transport events table or carrier entity
- Prices: Partial
  Evidence: coffee_price_history.py, market.py, lot.price_per_kg
  Gap: No first-class price quote per lot/deal; no historical price per lot
- Quality data: Complete
  Evidence: cupping.py, quality_alert.py
- General data for lots/cooperatives: Complete
  Evidence: meta JSON fields in cooperative.py and lot.py
- Regions: Partial
  Evidence: region.py and peru_region.py
  Gap: PeruRegion is a parallel knowledge base without foreign keys to Cooperatives or Lots
- Provenance: Partial
  Evidence: source.py, evidence.py
  Gap: Evidence currently targets cooperative/roaster only (no lot/shipment evidence)
- Data quality: Complete
  Evidence: data_quality_flag.py, routes/data_quality.py
- Audit and versioning: Complete
  Evidence: audit_log.py, entity_version.py
- RBAC: Complete
  Evidence: app/api/deps.py (require_role), auth routes
- UI baseline: Partial
  Evidence: Next.js pages in apps/web/app
  Gap: Build errors recently fixed in UI; still needs a clean build pass

High-Impact Gaps and Risks
- Deal model missing
  Evidence: services reference app.models.deal, but model file does not exist
  Risk: ML data collection and any deal-driven pricing logic will fail
- Shipment modeling conflict
  Evidence: Shipment.lot_id plus shipment_lots join table
  Risk: Inconsistent data when both are used; unclear single vs multi-lot shipments
- Transport normalization missing
  Evidence: tracking_events stored as JSON
  Risk: Limited analytics and query performance for tracking timelines
- Price lineage is weak
  Evidence: MarketObservation and CoffeePriceHistory exist, but no price quote per lot or deal
  Risk: Hard to reconcile margin calculations with market data and observed deals
- Provenance is not field-level
  Evidence: EntityEvidence is entity-level and limited to cooperative/roaster
  Risk: Hard to answer "why do we believe this specific value"
- Region duplication
  Evidence: Region and PeruRegion are separate, not linked
  Risk: Duplicated data entry and inconsistent region usage
- Shipment dates stored as string
  Evidence: shipment.py date fields are String
  Risk: Querying by date and sorting will be incorrect or slow

Recommended Next Actions (Milestone 1 Closure)
- Add Deal model and migrations, wire to ML and pricing paths
- Normalize shipments by choosing one model
  Option A: Keep shipment_lots and deprecate shipment.lot_id
  Option B: Keep shipment.lot_id and remove shipment_lots
- Create transport_events table (shipment_id, event_type, location, event_time, status)
- Add price_quotes table (lot_id, source_id, price, currency, observed_at)
- Extend EntityEvidence to support lot and shipment
- Link PeruRegion to Region or replace with Region
- Convert shipment date fields to Date or DateTime with migrations and backfill

Notes
- Encoding issues exist in some docs (README.md); not a functional blocker but should be cleaned.
