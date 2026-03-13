-- CoffeeStudio Full Stack Data Models Migration
-- Phase 1: Create 6 new tables + indexes
-- Run this in Supabase SQL Editor

-- ============================================
-- Table 1: weather_agronomic_data
-- ============================================
CREATE TABLE IF NOT EXISTS weather_agronomic_data (
    id SERIAL PRIMARY KEY,
    region VARCHAR(128) NOT NULL,
    country VARCHAR(64) NOT NULL DEFAULT 'Peru',
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    altitude_m INTEGER,
    observation_date DATE NOT NULL,
    temp_min_c FLOAT,
    temp_max_c FLOAT,
    temp_avg_c FLOAT,
    precipitation_mm FLOAT,
    precipitation_probability FLOAT,
    humidity_min FLOAT,
    humidity_max FLOAT,
    humidity_avg FLOAT,
    soil_moisture_index FLOAT,
    evapotranspiration_mm FLOAT,
    solar_radiation_mj FLOAT,
    wind_speed_kmh FLOAT,
    frost_risk FLOAT,
    drought_stress FLOAT,
    source VARCHAR(64) NOT NULL,
    source_id INTEGER,
    raw_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_weather_agronomic_region ON weather_agronomic_data(region);
CREATE INDEX IF NOT EXISTS ix_weather_agronomic_date ON weather_agronomic_data(observation_date);
CREATE INDEX IF NOT EXISTS ix_weather_agronomic_region_date ON weather_agronomic_data(region, observation_date);

-- ============================================
-- Table 2: social_sentiment_data
-- ============================================
CREATE TABLE IF NOT EXISTS social_sentiment_data (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(32) NOT NULL,
    source_url VARCHAR(512),
    author VARCHAR(128),
    content_text VARCHAR(4000),
    content_title VARCHAR(512),
    published_at TIMESTAMPTZ NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    sentiment_score FLOAT,
    sentiment_magnitude FLOAT,
    sentiment_label VARCHAR(16),
    topics JSONB,
    entities JSONB,
    likes_count INTEGER,
    comments_count INTEGER,
    shares_count INTEGER,
    market_relevance_score FLOAT,
    price_signal VARCHAR(16),
    language VARCHAR(8),
    meta JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_social_sentiment_platform ON social_sentiment_data(platform);
CREATE INDEX IF NOT EXISTS ix_social_sentiment_published ON social_sentiment_data(published_at);

-- ============================================
-- Table 3: shipment_api_events
-- ============================================
CREATE TABLE IF NOT EXISTS shipment_api_events (
    id SERIAL PRIMARY KEY,
    shipment_id INTEGER,
    vessel_imo VARCHAR(16),
    vessel_mmsi VARCHAR(16),
    vessel_name VARCHAR(128),
    vessel_type VARCHAR(64),
    vessel_flag VARCHAR(8),
    latitude FLOAT,
    longitude FLOAT,
    speed_knots FLOAT,
    course FLOAT,
    heading FLOAT,
    event_type VARCHAR(64) NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    port_code VARCHAR(16),
    port_name VARCHAR(128),
    port_country VARCHAR(64),
    eta_destination VARCHAR(128),
    eta_time TIMESTAMPTZ,
    source VARCHAR(32) NOT NULL,
    raw_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_shipment_api_events_shipment ON shipment_api_events(shipment_id);
CREATE INDEX IF NOT EXISTS ix_shipment_api_events_vessel ON shipment_api_events(vessel_imo);
CREATE INDEX IF NOT EXISTS ix_shipment_api_events_type ON shipment_api_events(event_type);
CREATE INDEX IF NOT EXISTS ix_shipment_api_events_time ON shipment_api_events(event_time);

-- ============================================
-- Table 4: ml_features_cache
-- ============================================
CREATE TABLE IF NOT EXISTS ml_features_cache (
    id SERIAL PRIMARY KEY,
    feature_set VARCHAR(64) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    entity_type VARCHAR(64),
    entity_id INTEGER,
    feature_date DATE NOT NULL,
    features JSONB NOT NULL,
    feature_names JSONB NOT NULL,
    feature_count INTEGER NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL,
    computation_time_ms INTEGER,
    missing_features JSONB,
    quality_score FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ml_features_cache_set ON ml_features_cache(feature_set);
CREATE INDEX IF NOT EXISTS ix_ml_features_cache_entity ON ml_features_cache(entity_id);
CREATE INDEX IF NOT EXISTS ix_ml_features_cache_date ON ml_features_cache(feature_date);
CREATE INDEX IF NOT EXISTS ix_ml_features_cache_set_date ON ml_features_cache(feature_set, feature_date);

-- ============================================
-- Table 5: data_lineage_log
-- ============================================
CREATE TABLE IF NOT EXISTS data_lineage_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(128) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(32) NOT NULL,
    action_time TIMESTAMPTZ NOT NULL,
    source_type VARCHAR(64) NOT NULL,
    source_name VARCHAR(128),
    source_url VARCHAR(512),
    actor_type VARCHAR(32) NOT NULL,
    actor_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    validation_status VARCHAR(32),
    validation_errors JSONB,
    meta JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_data_lineage_table ON data_lineage_log(table_name);
CREATE INDEX IF NOT EXISTS ix_data_lineage_record ON data_lineage_log(record_id);
CREATE INDEX IF NOT EXISTS ix_data_lineage_time ON data_lineage_log(action_time);

-- ============================================
-- Table 6: source_health_metrics
-- ============================================
CREATE TABLE IF NOT EXISTS source_health_metrics (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(64) NOT NULL,
    source_group VARCHAR(32) NOT NULL,
    metric_date DATE NOT NULL,
    metric_hour INTEGER,
    requests_total INTEGER NOT NULL DEFAULT 0,
    requests_successful INTEGER NOT NULL DEFAULT 0,
    requests_failed INTEGER NOT NULL DEFAULT 0,
    latency_min_ms INTEGER,
    latency_max_ms INTEGER,
    latency_avg_ms INTEGER,
    latency_p95_ms INTEGER,
    records_collected INTEGER NOT NULL DEFAULT 0,
    records_validated INTEGER NOT NULL DEFAULT 0,
    records_rejected INTEGER NOT NULL DEFAULT 0,
    error_types JSONB,
    last_error_message VARCHAR(512),
    circuit_breaker_status VARCHAR(16) NOT NULL DEFAULT 'closed',
    circuit_breaker_trips INTEGER NOT NULL DEFAULT 0,
    data_quality_score FLOAT,
    missing_fields_pct FLOAT,
    outliers_detected INTEGER,
    last_success_at TIMESTAMPTZ,
    last_failure_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_source_health_name ON source_health_metrics(source_name);
CREATE INDEX IF NOT EXISTS ix_source_health_date ON source_health_metrics(metric_date);
CREATE INDEX IF NOT EXISTS ix_source_health_name_date ON source_health_metrics(source_name, metric_date);

-- ============================================
-- Verify tables created
-- ============================================
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
