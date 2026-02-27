"""Freight prediction service using ML models."""

import os
from datetime import date, timedelta
from typing import Any
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.freight_model import FreightCostModel
from app.models.freight_history import FreightHistory
from app.models.ml_model import MLModel


class FreightPredictionService:
    """Service for freight cost and transit time predictions."""

    def __init__(self, db: Session):
        self.db = db
        self.model = FreightCostModel()
        self._load_active_model()

    def _load_active_model(self) -> None:
        """Load the active freight prediction model."""
        stmt = (
            select(MLModel)
            .where(MLModel.model_type == "freight_prediction")
            .where(MLModel.status == "active")
            .order_by(MLModel.training_date.desc())
            .limit(1)
        )
        result = self.db.execute(stmt)
        model_metadata = result.scalar_one_or_none()

        if model_metadata and os.path.exists(model_metadata.model_file_path):
            self.model.load(model_metadata.model_file_path)

    def _get_season(self, date_obj: date) -> str:
        """Get quarter/season from date."""
        month = date_obj.month
        if month in [1, 2, 3]:
            return "Q1"
        elif month in [4, 5, 6]:
            return "Q2"
        elif month in [7, 8, 9]:
            return "Q3"
        else:
            return "Q4"

    async def predict_freight_cost(
        self,
        origin_port: str,
        destination_port: str,
        weight_kg: int,
        container_type: str,
        departure_date: date,
    ) -> dict[str, Any]:
        """Predict freight cost using ML model.

        Args:
            origin_port: Origin port name
            destination_port: Destination port name
            weight_kg: Shipment weight in kg
            container_type: Container type (e.g., "20ft", "40ft")
            departure_date: Planned departure date

        Returns:
            Dictionary with prediction results and metadata
        """
        route = f"{origin_port}-{destination_port}"
        season = self._get_season(departure_date)

        # Get historical similar shipments for context
        stmt = (
            select(FreightHistory)
            .where(FreightHistory.route == route)
            .order_by(FreightHistory.departure_date.desc())
            .limit(10)
        )
        result = self.db.execute(stmt)
        similar_shipments = result.scalars().all()

        # Prepare input data
        input_data = pd.DataFrame(
            [
                {
                    "route": route,
                    "container_type": container_type,
                    "season": season,
                    "weight_kg": weight_kg,
                    "carrier": "Unknown",  # Not provided
                    "fuel_price_index": None,
                    "port_congestion_score": None,
                }
            ]
        )

        try:
            X, _ = self.model.prepare_features(input_data)
            predictions, lower, upper = self.model.predict_with_confidence(X)

            predicted_cost = float(predictions[0])
            confidence_low = float(max(0, lower[0]))
            confidence_high = float(upper[0])

            # Calculate confidence score based on similar shipments
            confidence_score = min(1.0, len(similar_shipments) / 10.0)

            factors = [
                "route",
                "weight",
                "container_type",
                "season",
                "historical_patterns",
            ]

            return {
                "predicted_cost_usd": predicted_cost,
                "confidence_interval_low": confidence_low,
                "confidence_interval_high": confidence_high,
                "confidence_score": confidence_score,
                "factors_considered": factors,
                "similar_historical_shipments": len(similar_shipments),
            }
        except Exception:
            # Fallback to simple average if model fails
            if similar_shipments:
                avg_cost = sum(s.freight_cost_usd for s in similar_shipments) / len(
                    similar_shipments
                )
                return {
                    "predicted_cost_usd": avg_cost,
                    "confidence_interval_low": avg_cost * 0.8,
                    "confidence_interval_high": avg_cost * 1.2,
                    "confidence_score": 0.5,
                    "factors_considered": ["historical_average"],
                    "similar_historical_shipments": len(similar_shipments),
                }
            else:
                # No data available
                return {
                    "predicted_cost_usd": 0.0,
                    "confidence_interval_low": 0.0,
                    "confidence_interval_high": 0.0,
                    "confidence_score": 0.0,
                    "factors_considered": ["no_data"],
                    "similar_historical_shipments": 0,
                }

    async def predict_transit_time(
        self, origin_port: str, destination_port: str, departure_date: date
    ) -> dict[str, Any]:
        """Predict transit time in days.

        Args:
            origin_port: Origin port name
            destination_port: Destination port name
            departure_date: Planned departure date

        Returns:
            Dictionary with transit time prediction
        """
        route = f"{origin_port}-{destination_port}"

        # Get historical transit times for this route
        stmt = (
            select(FreightHistory)
            .where(FreightHistory.route == route)
            .order_by(FreightHistory.departure_date.desc())
            .limit(20)
        )
        result = self.db.execute(stmt)
        historical = result.scalars().all()

        if historical:
            avg_transit = sum(h.transit_days for h in historical) / len(historical)
            min_transit = min(h.transit_days for h in historical)
            max_transit = max(h.transit_days for h in historical)

            return {
                "predicted_transit_days": int(avg_transit),
                "min_observed_days": min_transit,
                "max_observed_days": max_transit,
                "confidence_score": min(1.0, len(historical) / 20.0),
                "sample_size": len(historical),
            }
        else:
            return {
                "predicted_transit_days": 0,
                "min_observed_days": 0,
                "max_observed_days": 0,
                "confidence_score": 0.0,
                "sample_size": 0,
            }

    async def get_cost_trend(self, route: str, months_back: int = 12) -> dict[str, Any]:
        """Get historical cost trend for route.

        Args:
            route: Route identifier (e.g., "Callao-Hamburg")
            months_back: Number of months of history to retrieve

        Returns:
            Dictionary with trend data
        """
        cutoff_date = date.today() - timedelta(days=months_back * 30)

        stmt = (
            select(FreightHistory)
            .where(FreightHistory.route == route)
            .where(FreightHistory.departure_date >= cutoff_date)
            .order_by(FreightHistory.departure_date)
        )
        result = self.db.execute(stmt)
        historical = result.scalars().all()

        if not historical:
            return {
                "route": route,
                "trend_data": [],
                "average_cost": 0.0,
                "trend_direction": "unknown",
            }

        # Group by month
        monthly_data: dict[str, list[float]] = {}
        for record in historical:
            month_key = record.departure_date.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = []
            monthly_data[month_key].append(record.freight_cost_usd)

        trend_data: list[dict[str, Any]] = []
        for month, costs in sorted(monthly_data.items()):
            trend_data.append({"month": month, "average_cost": sum(costs) / len(costs)})

        avg_cost = sum(h.freight_cost_usd for h in historical) / len(historical)

        # Simple trend detection
        if len(trend_data) >= 2:
            first_half = trend_data[: len(trend_data) // 2]
            second_half = trend_data[len(trend_data) // 2 :]
            first_half_avg = sum(float(t["average_cost"]) for t in first_half) / len(
                first_half
            )
            second_half_avg = sum(float(t["average_cost"]) for t in second_half) / len(
                second_half
            )

            if second_half_avg > first_half_avg * 1.1:
                trend = "increasing"
            elif second_half_avg < first_half_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "route": route,
            "trend_data": trend_data,
            "average_cost": avg_cost,
            "trend_direction": trend,
        }

    def train_model(self, training_data: pd.DataFrame) -> dict[str, Any]:
        """Train or retrain the freight prediction model.

        Args:
            training_data: DataFrame with historical freight data

        Returns:
            Dictionary with training results and metrics
        """
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        import numpy as np

        X, y = self.model.prepare_features(training_data)

        if y is None or len(y) < 10:
            return {
                "status": "error",
                "message": "Insufficient training data",
            }

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Train model
        self.model.train(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        return {
            "status": "success",
            "mae": float(mae),
            "rmse": float(rmse),
            "r2_score": float(r2),
            "training_samples": len(X_train),
            "test_samples": len(X_test),
        }
