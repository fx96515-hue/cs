"""Full Stack Data Models + ML Seed Data.

Phase 1 of CoffeeStudio Full Stack Data Integration.
Creates 6 new tables for advanced ML features and monitoring.
Adds historical seed data for ML model training.

Revision ID: 0020_full_stack_data_models
Revises: 0019_milestone1_gap_close
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from datetime import date, datetime, timedelta
import random

revision = "0020_full_stack_data_models"
down_revision = "0019_milestone1_gap_close"
branch_labels = None
depends_on = None


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _create_weather_agronomic_data(inspector) -> None:
    if _table_exists(inspector, "weather_agronomic_data"):
        return

    op.create_table(
        "weather_agronomic_data",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("region", sa.String(128), nullable=False, index=True),
        sa.Column("country", sa.String(64), nullable=False, server_default="Peru"),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("altitude_m", sa.Integer(), nullable=True),
        sa.Column("observation_date", sa.Date(), nullable=False, index=True),
        sa.Column("temp_min_c", sa.Float(), nullable=True),
        sa.Column("temp_max_c", sa.Float(), nullable=True),
        sa.Column("temp_avg_c", sa.Float(), nullable=True),
        sa.Column("precipitation_mm", sa.Float(), nullable=True),
        sa.Column("precipitation_probability", sa.Float(), nullable=True),
        sa.Column("humidity_min", sa.Float(), nullable=True),
        sa.Column("humidity_max", sa.Float(), nullable=True),
        sa.Column("humidity_avg", sa.Float(), nullable=True),
        sa.Column("soil_moisture_index", sa.Float(), nullable=True),
        sa.Column("evapotranspiration_mm", sa.Float(), nullable=True),
        sa.Column("solar_radiation_mj", sa.Float(), nullable=True),
        sa.Column("wind_speed_kmh", sa.Float(), nullable=True),
        sa.Column("frost_risk", sa.Float(), nullable=True),
        sa.Column("drought_stress", sa.Float(), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_weather_agronomic_region_date", "weather_agronomic_data", ["region", "observation_date"])


def _create_social_sentiment_data(inspector) -> None:
    if _table_exists(inspector, "social_sentiment_data"):
        return

    op.create_table(
        "social_sentiment_data",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("platform", sa.String(32), nullable=False, index=True),
        sa.Column("source_url", sa.String(512), nullable=True),
        sa.Column("author", sa.String(128), nullable=True),
        sa.Column("content_text", sa.String(4000), nullable=True),
        sa.Column("content_title", sa.String(512), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("sentiment_magnitude", sa.Float(), nullable=True),
        sa.Column("sentiment_label", sa.String(16), nullable=True),
        sa.Column("topics", sa.JSON(), nullable=True),
        sa.Column("entities", sa.JSON(), nullable=True),
        sa.Column("likes_count", sa.Integer(), nullable=True),
        sa.Column("comments_count", sa.Integer(), nullable=True),
        sa.Column("shares_count", sa.Integer(), nullable=True),
        sa.Column("market_relevance_score", sa.Float(), nullable=True),
        sa.Column("price_signal", sa.String(16), nullable=True),
        sa.Column("language", sa.String(8), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def _create_shipment_api_events(inspector) -> None:
    if _table_exists(inspector, "shipment_api_events"):
        return

    op.create_table(
        "shipment_api_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shipment_id", sa.Integer(), sa.ForeignKey("shipments.id"), nullable=True, index=True),
        sa.Column("vessel_imo", sa.String(16), nullable=True, index=True),
        sa.Column("vessel_mmsi", sa.String(16), nullable=True),
        sa.Column("vessel_name", sa.String(128), nullable=True),
        sa.Column("vessel_type", sa.String(64), nullable=True),
        sa.Column("vessel_flag", sa.String(8), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("speed_knots", sa.Float(), nullable=True),
        sa.Column("course", sa.Float(), nullable=True),
        sa.Column("heading", sa.Float(), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False, index=True),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("port_code", sa.String(16), nullable=True),
        sa.Column("port_name", sa.String(128), nullable=True),
        sa.Column("port_country", sa.String(64), nullable=True),
        sa.Column("eta_destination", sa.String(128), nullable=True),
        sa.Column("eta_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def _create_ml_features_cache(inspector) -> None:
    if _table_exists(inspector, "ml_features_cache"):
        return

    op.create_table(
        "ml_features_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("feature_set", sa.String(64), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("entity_type", sa.String(64), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True, index=True),
        sa.Column("feature_date", sa.Date(), nullable=False, index=True),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("feature_names", sa.JSON(), nullable=False),
        sa.Column("feature_count", sa.Integer(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("computation_time_ms", sa.Integer(), nullable=True),
        sa.Column("missing_features", sa.JSON(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ml_features_cache_set_date", "ml_features_cache", ["feature_set", "feature_date"])


def _create_data_lineage_log(inspector) -> None:
    if _table_exists(inspector, "data_lineage_log"):
        return

    op.create_table(
        "data_lineage_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("table_name", sa.String(128), nullable=False, index=True),
        sa.Column("record_id", sa.Integer(), nullable=False, index=True),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("action_time", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("source_name", sa.String(128), nullable=True),
        sa.Column("source_url", sa.String(512), nullable=True),
        sa.Column("actor_type", sa.String(32), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("old_values", sa.JSON(), nullable=True),
        sa.Column("new_values", sa.JSON(), nullable=True),
        sa.Column("validation_status", sa.String(32), nullable=True),
        sa.Column("validation_errors", sa.JSON(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def _create_source_health_metrics(inspector) -> None:
    if _table_exists(inspector, "source_health_metrics"):
        return

    op.create_table(
        "source_health_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_name", sa.String(64), nullable=False, index=True),
        sa.Column("source_group", sa.String(32), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False, index=True),
        sa.Column("metric_hour", sa.Integer(), nullable=True),
        sa.Column("requests_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requests_successful", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requests_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_min_ms", sa.Integer(), nullable=True),
        sa.Column("latency_max_ms", sa.Integer(), nullable=True),
        sa.Column("latency_avg_ms", sa.Integer(), nullable=True),
        sa.Column("latency_p95_ms", sa.Integer(), nullable=True),
        sa.Column("records_collected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_validated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_types", sa.JSON(), nullable=True),
        sa.Column("last_error_message", sa.String(512), nullable=True),
        sa.Column("circuit_breaker_status", sa.String(16), nullable=False, server_default="closed"),
        sa.Column("circuit_breaker_trips", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("data_quality_score", sa.Float(), nullable=True),
        sa.Column("missing_fields_pct", sa.Float(), nullable=True),
        sa.Column("outliers_detected", sa.Integer(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_source_health_metrics_name_date", "source_health_metrics", ["source_name", "metric_date"])


def _seed_freight_history(connection) -> None:
    """Seed 100+ realistic freight history records for ML training."""
    
    routes = [
        ("Callao, Peru", "Hamburg, Germany", "PECLL-DEHAM"),
        ("Callao, Peru", "Bremen, Germany", "PECLL-DEBRE"),
        ("Callao, Peru", "Antwerp, Belgium", "PECLL-BEANR"),
        ("Callao, Peru", "Rotterdam, Netherlands", "PECLL-NLRTM"),
        ("Paita, Peru", "Hamburg, Germany", "PEPAI-DEHAM"),
    ]
    
    carriers = ["Hapag-Lloyd", "Maersk", "MSC", "CMA CGM", "ONE", "Evergreen"]
    container_types = ["20ft", "40ft", "40ft_HC"]
    
    records = []
    base_date = date(2024, 1, 1)
    
    for i in range(120):
        origin_port, dest_port, route = random.choice(routes)
        carrier = random.choice(carriers)
        container_type = random.choice(container_types)
        
        # Realistic weight based on container
        if container_type == "20ft":
            weight_kg = random.randint(15000, 22000)
            base_cost = random.uniform(2800, 3800)
        elif container_type == "40ft":
            weight_kg = random.randint(20000, 28000)
            base_cost = random.uniform(4200, 5500)
        else:  # 40ft_HC
            weight_kg = random.randint(22000, 30000)
            base_cost = random.uniform(4500, 5800)
        
        # Add seasonal variation
        month = (i % 12) + 1
        if month in [6, 7, 8]:  # Peak season
            base_cost *= random.uniform(1.1, 1.25)
        elif month in [1, 2]:  # Low season
            base_cost *= random.uniform(0.85, 0.95)
        
        # Transit days based on route
        if "DEHAM" in route or "DEBRE" in route:
            transit_days = random.randint(28, 35)
        else:
            transit_days = random.randint(25, 32)
        
        departure_date = base_date + timedelta(days=i * 3)
        arrival_date = departure_date + timedelta(days=transit_days)
        
        season = f"Q{((departure_date.month - 1) // 3) + 1}"
        
        fuel_price_index = random.uniform(80, 150)
        port_congestion = random.uniform(20, 80)
        
        records.append({
            "route": route,
            "origin_port": origin_port,
            "destination_port": dest_port,
            "carrier": carrier,
            "container_type": container_type,
            "weight_kg": weight_kg,
            "freight_cost_usd": round(base_cost, 2),
            "transit_days": transit_days,
            "departure_date": departure_date,
            "arrival_date": arrival_date,
            "season": season,
            "fuel_price_index": round(fuel_price_index, 2),
            "port_congestion_score": round(port_congestion, 2),
        })
    
    if records:
        connection.execute(
            sa.text("""
                INSERT INTO freight_history 
                (route, origin_port, destination_port, carrier, container_type, weight_kg, 
                 freight_cost_usd, transit_days, departure_date, arrival_date, season,
                 fuel_price_index, port_congestion_score)
                VALUES 
                (:route, :origin_port, :destination_port, :carrier, :container_type, :weight_kg,
                 :freight_cost_usd, :transit_days, :departure_date, :arrival_date, :season,
                 :fuel_price_index, :port_congestion_score)
            """),
            records
        )


def _seed_coffee_price_history(connection) -> None:
    """Seed 150+ realistic coffee price history records for ML training."""
    
    peru_regions = [
        ("Peru", "Cajamarca", -6.7, 1600),
        ("Peru", "Junin", -11.5, 1400),
        ("Peru", "San Martin", -6.5, 1200),
        ("Peru", "Cusco", -13.5, 1500),
        ("Peru", "Amazonas", -6.2, 1700),
        ("Peru", "Puno", -15.8, 1350),
    ]
    
    varieties = ["Typica", "Bourbon", "Caturra", "Catuai", "Geisha", "Catimor"]
    process_methods = ["Washed", "Natural", "Honey", "Semi-Washed"]
    quality_grades = ["Specialty", "Premium", "Standard", "Grade 1", "Grade 2"]
    certifications_options = [
        ["Organic"],
        ["Fair Trade"],
        ["Organic", "Fair Trade"],
        ["Rainforest Alliance"],
        ["UTZ"],
        [],
    ]
    
    records = []
    base_date = date(2023, 6, 1)
    
    # Base ICE C price trend (realistic values in USD/lb)
    ice_c_base = 1.85
    
    for i in range(180):
        country, region, lat, altitude = random.choice(peru_regions)
        variety = random.choice(varieties)
        process_method = random.choice(process_methods)
        quality_grade = random.choice(quality_grades)
        certifications = random.choice(certifications_options)
        
        # Cupping score based on quality grade and variety
        if quality_grade == "Specialty":
            cupping_score = random.uniform(84, 90)
        elif quality_grade == "Premium":
            cupping_score = random.uniform(80, 85)
        else:
            cupping_score = random.uniform(75, 82)
        
        if variety == "Geisha":
            cupping_score = min(92, cupping_score + random.uniform(2, 5))
        
        # ICE C price with trend and volatility
        ice_c_variation = random.uniform(-0.15, 0.20)
        trend = (i / 180) * 0.30  # Slight upward trend
        ice_c_price = ice_c_base + ice_c_variation + trend
        
        # Differential based on quality and certifications
        base_differential = 0.20
        if quality_grade == "Specialty":
            base_differential += random.uniform(0.30, 0.80)
        elif quality_grade == "Premium":
            base_differential += random.uniform(0.15, 0.35)
        
        if "Organic" in certifications:
            base_differential += random.uniform(0.10, 0.25)
        if "Fair Trade" in certifications:
            base_differential += random.uniform(0.05, 0.15)
        
        if variety == "Geisha":
            base_differential += random.uniform(1.0, 3.0)
        
        price_usd_per_lb = ice_c_price + base_differential
        price_usd_per_kg = price_usd_per_lb * 2.20462
        
        observation_date = base_date + timedelta(days=i * 2)
        
        market_sources = ["actual_trade", "market_estimate", "futures"]
        market_source = random.choices(market_sources, weights=[0.6, 0.3, 0.1])[0]
        
        records.append({
            "date": observation_date,
            "origin_country": country,
            "origin_region": region,
            "variety": variety,
            "process_method": process_method,
            "quality_grade": quality_grade,
            "cupping_score": round(cupping_score, 1),
            "certifications": certifications,
            "price_usd_per_kg": round(price_usd_per_kg, 2),
            "price_usd_per_lb": round(price_usd_per_lb, 2),
            "ice_c_price_usd_per_lb": round(ice_c_price, 4),
            "differential_usd_per_lb": round(base_differential, 4),
            "market_source": market_source,
            "market_key": "COFFEE_C:USD_LB",
        })
    
    if records:
        for record in records:
            record["certifications"] = str(record["certifications"]).replace("'", '"') if record["certifications"] else "[]"
        
        connection.execute(
            sa.text("""
                INSERT INTO coffee_price_history 
                (date, origin_country, origin_region, variety, process_method, quality_grade,
                 cupping_score, certifications, price_usd_per_kg, price_usd_per_lb,
                 ice_c_price_usd_per_lb, differential_usd_per_lb, market_source, market_key)
                VALUES 
                (:date, :origin_country, :origin_region, :variety, :process_method, :quality_grade,
                 :cupping_score, CAST(:certifications AS JSON), :price_usd_per_kg, :price_usd_per_lb,
                 :ice_c_price_usd_per_lb, :differential_usd_per_lb, :market_source, :market_key)
            """),
            records
        )


def _seed_market_observations(connection) -> None:
    """Seed 200+ market observations (FX, coffee prices, etc.) for ML features."""
    
    records = []
    base_date = datetime(2023, 6, 1, 12, 0, 0)
    
    # FX rates with realistic values
    fx_pairs = [
        ("FX:EUR_USD", 1.08, 0.05),
        ("FX:EUR_PEN", 4.05, 0.20),
        ("FX:EUR_BRL", 5.30, 0.30),
        ("FX:EUR_GBP", 0.86, 0.03),
    ]
    
    # Coffee prices
    coffee_keys = [
        ("COFFEE_C:USD_LB", 1.85, 0.25),
        ("COFFEE_ROBUSTA:USD_MT", 2400, 300),
    ]
    
    # Freight indices
    freight_keys = [
        ("FREIGHT:PERU_EU_40FT", 4500, 800),
        ("FREIGHT:PERU_EU_20FT", 3200, 500),
    ]
    
    for i in range(250):
        obs_time = base_date + timedelta(days=i)
        
        # FX observations
        for key, base_value, volatility in fx_pairs:
            trend = (i / 250) * 0.05  # Small trend
            value = base_value + random.uniform(-volatility, volatility) + trend
            records.append({
                "key": key,
                "value": round(value, 4),
                "unit": key.split(":")[1].split("_")[1],
                "currency": key.split(":")[1].split("_")[0],
                "observed_at": obs_time,
            })
        
        # Coffee observations (daily)
        for key, base_value, volatility in coffee_keys:
            trend = (i / 250) * 0.15
            value = base_value + random.uniform(-volatility, volatility) + trend
            unit = "USD/LB" if "LB" in key else "USD/MT"
            records.append({
                "key": key,
                "value": round(value, 4),
                "unit": unit,
                "currency": "USD",
                "observed_at": obs_time,
            })
        
        # Freight observations (weekly)
        if i % 7 == 0:
            for key, base_value, volatility in freight_keys:
                value = base_value + random.uniform(-volatility, volatility)
                records.append({
                    "key": key,
                    "value": round(value, 2),
                    "unit": "USD",
                    "currency": "USD",
                    "observed_at": obs_time,
                })
    
    if records:
        connection.execute(
            sa.text("""
                INSERT INTO market_observations 
                (key, value, unit, currency, observed_at)
                VALUES 
                (:key, :value, :unit, :currency, :observed_at)
            """),
            records
        )


def _seed_test_entities(connection) -> None:
    """Seed test cooperatives, roasters, lots for integration testing."""
    
    # Cooperatives
    cooperatives = [
        {"name": "Cooperativa Agraria Cafetalera Valle del Sandia", "country": "Peru", "region": "Puno", "certified_organic": True, "certified_fairtrade": True},
        {"name": "Cooperativa Sol y Cafe", "country": "Peru", "region": "Cajamarca", "certified_organic": True, "certified_fairtrade": False},
        {"name": "Central de Cooperativas Agrarias Cafetaleras", "country": "Peru", "region": "Junin", "certified_organic": False, "certified_fairtrade": True},
        {"name": "Cooperativa Agraria Norandino", "country": "Peru", "region": "Piura", "certified_organic": True, "certified_fairtrade": True},
        {"name": "Cooperativa La Florida", "country": "Peru", "region": "Amazonas", "certified_organic": True, "certified_fairtrade": False},
    ]
    
    connection.execute(
        sa.text("""
            INSERT INTO cooperatives (name, country, region, certified_organic, certified_fairtrade)
            VALUES (:name, :country, :region, :certified_organic, :certified_fairtrade)
            ON CONFLICT DO NOTHING
        """),
        cooperatives
    )
    
    # Roasters
    roasters = [
        {"name": "Rösterei Schwarzbrand", "country": "Germany", "city": "Berlin", "specialty_focus": True},
        {"name": "Kaffeerösterei Mokkaflor", "country": "Germany", "city": "Hamburg", "specialty_focus": True},
        {"name": "Röstwerk München", "country": "Germany", "city": "Munich", "specialty_focus": False},
    ]
    
    connection.execute(
        sa.text("""
            INSERT INTO roasters (name, country, city, specialty_focus)
            VALUES (:name, :country, :city, :specialty_focus)
            ON CONFLICT DO NOTHING
        """),
        roasters
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Create new tables
    _create_weather_agronomic_data(inspector)
    _create_social_sentiment_data(inspector)
    _create_shipment_api_events(inspector)
    _create_ml_features_cache(inspector)
    _create_data_lineage_log(inspector)
    _create_source_health_metrics(inspector)
    
    # Seed ML training data
    connection = bind.connect()
    
    try:
        _seed_freight_history(connection)
        _seed_coffee_price_history(connection)
        _seed_market_observations(connection)
        _seed_test_entities(connection)
        connection.commit()
    except Exception as e:
        connection.rollback()
        print(f"Seed data error (may already exist): {e}")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    
    tables_to_drop = [
        "source_health_metrics",
        "data_lineage_log", 
        "ml_features_cache",
        "shipment_api_events",
        "social_sentiment_data",
        "weather_agronomic_data",
    ]
    
    for table in tables_to_drop:
        if _table_exists(inspector, table):
            op.drop_table(table)
