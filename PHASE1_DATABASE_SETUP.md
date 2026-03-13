# CoffeeStudio Phase 1: Database Setup Instructions

## Step 1: Create Tables in Supabase

1. Go to your Supabase Dashboard: https://supabase.com/dashboard
2. Open your Project "cs"
3. Click on "SQL Editor" in the left sidebar
4. Click "New Query"
5. Copy and paste the entire content from: `/scripts/0020_full_stack_tables.sql`
6. Click "Run" (or Ctrl+Enter)
7. You should see: "✓ 6 tables created successfully"

## Step 2: Verify Tables Created

Run this verification query:
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'weather_agronomic_data',
    'social_sentiment_data', 
    'shipment_api_events',
    'ml_features_cache',
    'data_lineage_log',
    'source_health_metrics'
)
ORDER BY table_name;
```

Expected result: 6 rows with all table names listed

## Step 3: Load Seed Data

1. In Supabase SQL Editor, click "New Query" again
2. Copy and paste the entire content from: `/scripts/0021_seed_ml_training_data.sql`
3. Click "Run"
4. You should see: "✓ 180 seed records loaded"

## Database Schema

### Table 1: weather_agronomic_data (180 records)
- 6 Peru regions × 30 days of meteorological data
- Columns: region, temp, precipitation, soil_moisture, evapotranspiration, etc.

### Table 2: social_sentiment_data (30 records)
- Twitter, Reddit, Coffee Blogs sentiment
- Columns: platform, sentiment_score, market_relevance, price_signal, etc.

### Table 3: shipment_api_events (40 records)
- Vessel tracking data
- Columns: vessel_imo, latitude, longitude, eta, port_code, event_type, etc.

### Table 4: ml_features_cache (30 records)
- Pre-computed ML features for training
- Columns: feature_set, entity_type, features (JSONB), quality_score, etc.

### Table 5: data_lineage_log (20 records)
- Data source tracking & audit trail
- Columns: table_name, record_id, source_name, validation_status, etc.

### Table 6: source_health_metrics (17 records)
- Health metrics for all 17 data sources
- Columns: source_name, requests_total, latency_avg, circuit_breaker_status, etc.

## Total Records
- **180 seed records** loaded for Phase 2 data pipeline integration

## Next Steps
- Phase 2: Build Provider Modules (9 modules for 17 APIs)
- Phase 3: Feature Engineering (50+ ML features)
- Phase 4: Scheduling & Monitoring
