Data Model ERD and Migration Plan
Date: 2026-02-28

Current Core ERD (Mermaid)
```mermaid
erDiagram
    COOPERATIVES {
        int id PK
        string name
        int region_id FK
        float quality_score
        float confidence
        string status
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }

    ROASTERS {
        int id PK
        string name
        string city
        string status
        float total_score
        float confidence
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }

    LOTS {
        int id PK
        int cooperative_id FK
        string name
        int crop_year
        float price_per_kg
        string currency
        float weight_kg
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }

    SHIPMENTS {
        int id PK
        int lot_id
        int cooperative_id
        int roaster_id
        string container_number
        string bill_of_lading
        float weight_kg
        string status
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }

    SHIPMENT_LOTS {
        int id PK
        int shipment_id FK
        int lot_id FK
        float weight_kg
        datetime created_at
    }

    REGIONS {
        int id PK
        string name
        string country
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }

    CUPPING_RESULTS {
        int id PK
        int cooperative_id
        int lot_id
        int roaster_id
        float sca_score
        datetime occurred_at
    }

    MARGIN_RUNS {
        int id PK
        int lot_id FK
        string profile
        datetime computed_at
    }

    SOURCES {
        int id PK
        string name
        string kind
        float reliability
        datetime created_at
        datetime updated_at
    }

    MARKET_OBSERVATIONS {
        int id PK
        string key
        float value
        string unit
        string currency
        datetime observed_at
        int source_id FK
    }

    ENTITY_EVIDENCE {
        int id PK
        string entity_type
        int entity_id
        int source_id
        string evidence_url
        datetime extracted_at
    }

    DATA_QUALITY_FLAGS {
        int id PK
        string entity_type
        int entity_id
        string issue_type
        string severity
        datetime detected_at
        datetime resolved_at
    }

    ENTITY_VERSIONS {
        int id PK
        string entity_type
        int entity_id
        int version
        datetime created_at
    }

    AUDIT_LOGS {
        int id PK
        string action
        string entity_type
        int entity_id
        datetime created_at
    }

    USERS {
        int id PK
        string email
        string role
        bool is_active
        datetime created_at
    }

    COOPERATIVES ||--o{ LOTS : has
    COOPERATIVES ||--o{ SHIPMENTS : ships
    ROASTERS ||--o{ SHIPMENTS : receives
    LOTS ||--o{ SHIPMENT_LOTS : assigned
    SHIPMENTS ||--o{ SHIPMENT_LOTS : contains
    REGIONS ||--o{ COOPERATIVES : in
    LOTS ||--o{ MARGIN_RUNS : priced
    COOPERATIVES ||--o{ CUPPING_RESULTS : cupped
    ROASTERS ||--o{ CUPPING_RESULTS : cupped
    LOTS ||--o{ CUPPING_RESULTS : cupped
    SOURCES ||--o{ MARKET_OBSERVATIONS : provides
    SOURCES ||--o{ ENTITY_EVIDENCE : provides
```

Supporting Tables (Current)
- COFFEE_PRICE_HISTORY: historical prices for ML training
- FREIGHT_HISTORY: historical freight data for ML training
- QUALITY_ALERTS: quality change alerts (entity_type, entity_id)
- ENTITY_ALIASES: dedup and search aliases
- ENTITY_EVENTS: lifecycle events
- SENTIMENT_SCORES: sentiment signal
- NEWS_ITEMS: news ingestion
- REPORTS: generated reports
- WEB_EXTRACTS: web content extracts
- KNOWLEDGE_DOCS: knowledge base items
- ML_MODELS and ML_PREDICTIONS: model metadata and forecast outputs
- PERU_REGIONS: knowledge base for Peru regions (parallel to REGIONS)

Target Model Extensions (to close Milestone 1 gaps)
- DEALS: first-class transactions with pricing, volume, and closure status
- PRICE_QUOTES: per-lot or per-deal quotes linked to SOURCES
- TRANSPORT_EVENTS: normalized shipment events with timestamps and locations
- FIELD_EVIDENCE: field-level provenance (entity_type, entity_id, field_name)
- SOURCE_LINKS: explicit FK from DATA_QUALITY_FLAGS to SOURCES
- REGION_UNIFICATION: merge PERU_REGIONS into REGIONS or add FK references

Migration Plan (Phased)
1. Schema additions: Add deals table with FK to cooperative, roaster, lot. Add transport_events table with FK to shipments. Add price_quotes table with FK to lot and source. Add field_evidence table or extend entity_evidence with field_name.
2. Schema cleanup: Decide between shipment.lot_id and shipment_lots, then deprecate one. Convert shipment date strings to Date or DateTime. Add FK on data_quality_flags.source_id (nullable).
3. Data backfill: Migrate shipment.lot_id rows into shipment_lots if many-to-many is chosen. Parse shipment date strings into typed columns. Backfill price_quotes from lot.price_per_kg and market_observations.
4. Application alignment: Update services to read and write new tables. Update API schemas and routes for deals, quotes, transport events. Update UI to show normalized transport timelines and price lineage.
5. Validation and rollout: Add migration tests (upgrade and downgrade). Backfill verification queries and counts. Deploy with feature flags for new endpoints.
