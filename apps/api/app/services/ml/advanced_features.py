"""
Advanced ML feature engineering helpers derived from PR721.

These helpers are intentionally pure-python and side-effect free so they can be
integrated safely into the current backend without DB or worker changes.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np


class FreightFeatureEngine:
    """Generate freight-specific engineered features."""

    @staticmethod
    def compute_fuel_price_index(fx_rate: float, base_price: float = 100.0) -> float:
        return base_price * (1.0 + (fx_rate - 1.0) * 0.5)

    @staticmethod
    def compute_port_congestion_score(
        vessels_in_port: int,
        avg_wait_hours: int,
        max_capacity: int = 50,
    ) -> float:
        utilization = min(vessels_in_port / max_capacity, 1.0)
        wait_factor = min(avg_wait_hours / 48, 1.0)
        return round((utilization * 0.6) + (wait_factor * 0.4), 4)

    @staticmethod
    def compute_seasonal_demand_index(month: int) -> float:
        if month in [6, 7, 8, 9]:
            return 0.9
        if month in [5, 10]:
            return 0.7
        return 0.5

    @staticmethod
    def compute_carrier_reliability_score(
        on_time_deliveries: int,
        total_deliveries: int,
    ) -> float:
        if total_deliveries == 0:
            return 0.75
        return round(min(on_time_deliveries / total_deliveries, 1.0), 4)

    @staticmethod
    def compute_route_complexity(distance_km: float, stops: int) -> float:
        distance_factor = min(distance_km / 15000, 1.0)
        stops_factor = min(stops / 5, 1.0)
        return round((distance_factor * 0.6) + (stops_factor * 0.4), 4)

    @staticmethod
    def compute_exchange_rate_volatility(recent_rates: list[float]) -> float:
        if len(recent_rates) < 2:
            return 0.02
        mean = float(np.mean(recent_rates))
        if mean == 0:
            return 0.0
        return round(float(np.std(recent_rates) / mean), 4)

    @staticmethod
    def compute_weather_delay_probability(
        precipitation_mm: float,
        wind_speed_kmh: float,
        temp_c: float,
    ) -> float:
        rain_factor = min(precipitation_mm / 100, 1.0) * 0.4
        wind_factor = min(max(wind_speed_kmh - 40, 0) / 50, 1.0) * 0.4
        temp_factor = (1.0 if temp_c < 0 or temp_c > 45 else 0.0) * 0.2
        return round(rain_factor + wind_factor + temp_factor, 4)

    @staticmethod
    def generate_all_freight_features(record: dict) -> dict[str, float]:
        return {
            "fuel_price_index": FreightFeatureEngine.compute_fuel_price_index(
                float(record.get("fx_rate", 1.0))
            ),
            "port_congestion_score": FreightFeatureEngine.compute_port_congestion_score(
                int(record.get("vessels_in_port", 20)),
                int(record.get("avg_wait_hours", 12)),
            ),
            "seasonal_demand_index": FreightFeatureEngine.compute_seasonal_demand_index(
                datetime.utcnow().month
            ),
            "carrier_reliability_score": FreightFeatureEngine.compute_carrier_reliability_score(
                int(record.get("on_time_deliveries", 45)),
                int(record.get("total_deliveries", 50)),
            ),
            "route_complexity": FreightFeatureEngine.compute_route_complexity(
                float(record.get("distance_km", 12000)),
                int(record.get("stops", 2)),
            ),
            "exchange_rate_volatility": FreightFeatureEngine.compute_exchange_rate_volatility(
                [1.08, 1.09, 1.07, 1.10]
            ),
            "weather_delay_probability": FreightFeatureEngine.compute_weather_delay_probability(
                float(record.get("precipitation_mm", 10)),
                float(record.get("wind_speed_kmh", 15)),
                float(record.get("temp_c", 20)),
            ),
            "container_availability": float(record.get("container_availability", 0.85)),
            "supply_disruption_risk": float(record.get("supply_disruption_risk", 0.15)),
            "geopolitical_risk": float(record.get("geopolitical_risk", 0.05)),
            "vessel_age_years": float(record.get("vessel_age_years", 8)),
            "recent_price_volatility": 0.08,
            "competitor_pricing_pressure": 0.12,
            "customs_risk_index": 0.10,
            "arrival_eta_confidence": 0.85,
        }


class PriceFeatureEngine:
    """Generate price-specific engineered features."""

    @staticmethod
    def compute_market_sentiment_score(
        twitter_sentiment: float,
        reddit_sentiment: float,
        news_sentiment: float,
    ) -> float:
        return round(
            (twitter_sentiment * 0.4)
            + (reddit_sentiment * 0.3)
            + (news_sentiment * 0.3),
            4,
        )

    @staticmethod
    def compute_frost_risk(temp_min: float) -> float:
        if temp_min < -5:
            return 1.0
        if temp_min < 0:
            return 0.8
        if temp_min < 5:
            return 0.3
        return 0.0

    @staticmethod
    def compute_drought_stress(soil_moisture: float, precip_mm: float) -> float:
        moisture_factor = 1.0 - soil_moisture if soil_moisture is not None else 0.5
        precip_factor = (
            max(0.0, 1.0 - (precip_mm / 50)) if precip_mm is not None else 0.5
        )
        return round((moisture_factor * 0.6) + (precip_factor * 0.4), 4)

    @staticmethod
    def compute_altitude_quality_index(altitude_m: int) -> float:
        if 1200 <= altitude_m <= 1800:
            return 1.0
        if 1000 <= altitude_m <= 2000:
            return 0.85
        return 0.6

    @staticmethod
    def generate_all_price_features(record: dict) -> dict[str, float]:
        return {
            "market_sentiment_score": PriceFeatureEngine.compute_market_sentiment_score(
                0.6, 0.55, 0.58
            ),
            "competing_suppliers_count": float(record.get("competing_suppliers", 35)),
            "quality_cupping_trend": float(record.get("cupping_score", 82)),
            "exchange_rate_impact_eur_usd": float(record.get("fx_eur_usd", 1.08)),
            "exchange_rate_impact_eur_pen": float(record.get("fx_eur_pen", 3.95)),
            "ice_futures_correlation": 0.92,
            "global_coffee_stock_level": float(record.get("global_stocks_bags", 78)),
            "peru_production_forecast": float(
                record.get("peru_prod_forecast_tons", 420000)
            ),
            "frost_risk_index": PriceFeatureEngine.compute_frost_risk(
                float(record.get("temp_min", 15))
            ),
            "drought_stress_index": PriceFeatureEngine.compute_drought_stress(
                float(record.get("soil_moisture", 0.65)),
                float(record.get("precip_mm", 50)),
            ),
            "pest_outbreak_probability": 0.12,
            "harvest_timing_indicator": 0.7,
            "certifications_premium": float(record.get("certifications_premium", 0.15)),
            "processing_method_marketability": 0.82,
            "altitude_quality_index": PriceFeatureEngine.compute_altitude_quality_index(
                int(record.get("altitude_m", 1500))
            ),
            "origin_reputation_score": 0.88,
            "news_buzz_index": 0.65,
            "shortage_signal_index": 0.18,
            "buyer_demand_index": 0.72,
            "price_elasticity_factor": 0.85,
        }


class CrossFeatureEngine:
    """Generate cross-domain features."""

    @staticmethod
    def compute_freight_to_price_ratio(
        freight_cost: float, coffee_price: float
    ) -> float:
        if coffee_price <= 0:
            return 0.0
        return round(freight_cost / coffee_price, 4)

    @staticmethod
    def compute_total_landed_cost(
        coffee_price: float,
        freight_cost: float,
        fx_rate: float,
        insurance_pct: float = 0.01,
    ) -> float:
        insurance = (coffee_price + freight_cost) * insurance_pct
        return round((coffee_price + freight_cost + insurance) * fx_rate, 4)

    @staticmethod
    def compute_deal_profitability_forecast(
        sell_price: float,
        landed_cost: float,
        margin_target_pct: float = 0.05,
    ) -> float:
        if landed_cost <= 0:
            return 0.0
        return round(((sell_price - landed_cost) / landed_cost) - margin_target_pct, 4)

    @staticmethod
    def generate_temporal_features() -> dict[str, float]:
        now = datetime.utcnow()
        month = now.month
        quarter = ((month - 1) // 3) + 1
        return {
            "month_of_year": float(month),
            "quarter": float(quarter),
            "is_harvest_season": 1.0 if month in [6, 7, 8, 9] else 0.0,
            "days_since_season_start": float(
                (now - datetime(now.year, 6, 1)).days % 365
            ),
            "is_weekend": 1.0 if now.weekday() >= 5 else 0.0,
        }

    @staticmethod
    def generate_all_cross_features(record: dict) -> dict[str, float]:
        landed_cost = CrossFeatureEngine.compute_total_landed_cost(
            float(record.get("coffee_price", 2.10)),
            float(record.get("freight_cost", 500)),
            float(record.get("fx_rate", 1.08)),
        )
        features = {
            "freight_to_price_ratio": CrossFeatureEngine.compute_freight_to_price_ratio(
                float(record.get("freight_cost", 500)),
                float(record.get("coffee_price", 2.10)),
            ),
            "total_landed_cost": landed_cost,
            "deal_profitability_forecast": CrossFeatureEngine.compute_deal_profitability_forecast(
                float(record.get("sell_price", 2.50)),
                landed_cost,
            ),
            "region_reputation_score": float(record.get("region_reputation", 0.88)),
            "buyer_roaster_preference_index": float(
                record.get("buyer_preference", 0.75)
            ),
            "supply_chain_efficiency": float(record.get("supply_efficiency", 0.82)),
        }
        features.update(CrossFeatureEngine.generate_temporal_features())
        return features


class FeatureEngineer:
    """Main feature engineering orchestrator."""

    @staticmethod
    def generate_all_features(
        record: dict, record_type: str = "price"
    ) -> dict[str, float]:
        features: dict[str, float] = {}
        if record_type == "freight":
            features.update(FreightFeatureEngine.generate_all_freight_features(record))
        elif record_type == "price":
            features.update(PriceFeatureEngine.generate_all_price_features(record))
        features.update(CrossFeatureEngine.generate_all_cross_features(record))
        return features

    @staticmethod
    def feature_catalog() -> dict[str, list[str]]:
        freight = list(FreightFeatureEngine.generate_all_freight_features({}).keys())
        price = list(PriceFeatureEngine.generate_all_price_features({}).keys())
        cross = list(CrossFeatureEngine.generate_all_cross_features({}).keys())
        return {
            "Fracht-Features": freight,
            "Preis-Features": price,
            "Cross-Features": cross,
        }
