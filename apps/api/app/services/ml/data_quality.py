"""
Data quality and anomaly helpers derived from PR721.
"""

from __future__ import annotations

from datetime import datetime
import statistics


class AnomalyDetector:
    @staticmethod
    def detect_price_anomalies(price_history: list[dict]) -> list[dict]:
        anomalies: list[dict] = []
        prices = [
            row.get("price") for row in price_history if row.get("price") is not None
        ]
        if len(prices) < 2:
            return anomalies

        for index in range(1, len(prices)):
            previous = prices[index - 1]
            current = prices[index]
            if previous and abs((current - previous) / previous) > 0.20:
                anomalies.append(
                    {
                        "type": "spike",
                        "index": index,
                        "previous_price": previous,
                        "current_price": current,
                    }
                )
        return anomalies

    @staticmethod
    def detect_shipping_anomalies(shipping_records: list[dict]) -> list[dict]:
        anomalies: list[dict] = []
        for index, record in enumerate(shipping_records):
            if record.get("delay_hours", 0) > 72:
                anomalies.append(
                    {
                        "type": "excessive_delay",
                        "index": index,
                        "delay_hours": record["delay_hours"],
                    }
                )
            if record.get("speed_knots", 0) > 50:
                anomalies.append(
                    {
                        "type": "excessive_speed",
                        "index": index,
                        "speed_knots": record["speed_knots"],
                    }
                )
        return anomalies

    @staticmethod
    def detect_weather_anomalies(weather_records: list[dict]) -> list[dict]:
        anomalies: list[dict] = []
        for index, record in enumerate(weather_records):
            temp_min = record.get("temp_min_c")
            temp_max = record.get("temp_max_c")
            if temp_min is not None and temp_max is not None and temp_min > temp_max:
                anomalies.append(
                    {
                        "type": "temp_inversion",
                        "index": index,
                        "temp_min": temp_min,
                        "temp_max": temp_max,
                    }
                )
            if record.get("precipitation_mm", 0) > 200:
                anomalies.append(
                    {
                        "type": "extreme_precipitation",
                        "index": index,
                        "precipitation_mm": record["precipitation_mm"],
                    }
                )
        return anomalies


class QualityReport:
    @staticmethod
    def generate_report(records: list[dict], data_type: str) -> dict:
        if not records:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "data_type": data_type,
                "total_records": 0,
                "quality_score": 0.0,
                "quality_label": "poor",
                "issues": ["No records to validate"],
                "recommendations": ["Import or generate data before validation"],
            }

        if data_type == "price":
            anomalies = AnomalyDetector.detect_price_anomalies(records)
        elif data_type == "freight":
            anomalies = AnomalyDetector.detect_shipping_anomalies(records)
        elif data_type == "weather":
            anomalies = AnomalyDetector.detect_weather_anomalies(records)
        else:
            anomalies = []

        quality_score = 1.0 - min(len(anomalies) / max(len(records), 1), 0.3)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "data_type": data_type,
            "total_records": len(records),
            "quality_score": round(quality_score, 4),
            "quality_label": (
                "excellent"
                if quality_score > 0.9
                else "good"
                if quality_score > 0.75
                else "fair"
                if quality_score > 0.5
                else "poor"
            ),
            "issues": [f"Found {len(anomalies)} anomalies"] if anomalies else [],
            "recommendations": (
                ["Review source data or collection process"]
                if len(anomalies) > len(records) * 0.1
                else []
            ),
            "anomaly_count": len(anomalies),
        }

    @staticmethod
    def mean_or_zero(values: list[float]) -> float:
        return float(statistics.mean(values)) if values else 0.0
