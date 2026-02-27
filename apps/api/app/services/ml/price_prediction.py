"""Coffee price prediction service using ML models."""

import os
from datetime import date
from typing import Any
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.price_model import CoffeePriceModel
from app.models.coffee_price_history import CoffeePriceHistory
from app.models.ml_model import MLModel


class CoffeePricePredictionService:
    """Service for coffee price predictions and forecasting."""

    def __init__(self, db: Session):
        self.db = db
        self.model = CoffeePriceModel()
        self._load_active_model()

    def _load_active_model(self) -> None:
        """Load the active price prediction model."""
        stmt = (
            select(MLModel)
            .where(MLModel.model_type == "price_prediction")
            .where(MLModel.status == "active")
            .order_by(MLModel.training_date.desc())
            .limit(1)
        )
        result = self.db.execute(stmt)
        model_metadata = result.scalar_one_or_none()

        if model_metadata and os.path.exists(model_metadata.model_file_path):
            self.model.load(model_metadata.model_file_path)

    async def predict_coffee_price(
        self,
        origin_country: str,
        origin_region: str,
        variety: str,
        process_method: str,
        quality_grade: str,
        cupping_score: float,
        certifications: list[str],
        forecast_date: date,
    ) -> dict[str, Any]:
        """Predict coffee price using ML model.

        Args:
            origin_country: Country of origin
            origin_region: Specific region
            variety: Coffee variety
            process_method: Processing method
            quality_grade: Quality grade
            cupping_score: Cupping score
            certifications: List of certifications
            forecast_date: Date for price forecast

        Returns:
            Dictionary with price prediction and metadata
        """
        # Get recent market context
        stmt = (
            select(CoffeePriceHistory)
            .where(CoffeePriceHistory.origin_country == origin_country)
            .where(CoffeePriceHistory.origin_region == origin_region)
            .order_by(CoffeePriceHistory.date.desc())
            .limit(20)
        )
        result = self.db.execute(stmt)
        historical = result.scalars().all()

        # Prepare input data
        input_data = pd.DataFrame(
            [
                {
                    "origin_country": origin_country,
                    "origin_region": origin_region,
                    "variety": variety,
                    "process_method": process_method,
                    "quality_grade": quality_grade,
                    "cupping_score": cupping_score,
                    "certifications": certifications,
                    "ice_c_price_usd_per_lb": 1.5,  # Default
                    "date": forecast_date,
                }
            ]
        )

        try:
            X, _ = self.model.prepare_features(input_data)
            predictions, lower, upper = self.model.predict_with_confidence(X)

            predicted_price = float(predictions[0])
            confidence_low = float(max(0, lower[0]))
            confidence_high = float(upper[0])

            # Calculate confidence based on data availability
            confidence_score = min(1.0, len(historical) / 20.0)

            # Compare with recent prices
            if historical:
                recent_avg = sum(h.price_usd_per_kg for h in historical[:5]) / min(
                    5, len(historical)
                )
                if predicted_price > recent_avg * 1.1:
                    comparison = "above_recent_average"
                elif predicted_price < recent_avg * 0.9:
                    comparison = "below_recent_average"
                else:
                    comparison = "near_recent_average"

                # Trend detection
                if len(historical) >= 10:
                    old_avg = sum(h.price_usd_per_kg for h in historical[-10:]) / 10
                    if recent_avg > old_avg * 1.05:
                        trend = "increasing"
                    elif recent_avg < old_avg * 0.95:
                        trend = "decreasing"
                    else:
                        trend = "stable"
                else:
                    trend = "insufficient_data"
            else:
                comparison = "no_historical_data"
                trend = "unknown"

            return {
                "predicted_price_usd_per_kg": predicted_price,
                "confidence_interval_low": confidence_low,
                "confidence_interval_high": confidence_high,
                "confidence_score": confidence_score,
                "market_comparison": comparison,
                "price_trend": trend,
            }
        except Exception:
            # Fallback to historical average
            if historical:
                avg_price = sum(h.price_usd_per_kg for h in historical) / len(
                    historical
                )
                return {
                    "predicted_price_usd_per_kg": avg_price,
                    "confidence_interval_low": avg_price * 0.9,
                    "confidence_interval_high": avg_price * 1.1,
                    "confidence_score": 0.5,
                    "market_comparison": "historical_average",
                    "price_trend": "unknown",
                }
            else:
                return {
                    "predicted_price_usd_per_kg": 0.0,
                    "confidence_interval_low": 0.0,
                    "confidence_interval_high": 0.0,
                    "confidence_score": 0.0,
                    "market_comparison": "no_data",
                    "price_trend": "unknown",
                }

    async def forecast_price_trend(
        self, origin_region: str, months_ahead: int = 6
    ) -> dict[str, Any]:
        """Forecast price trend for next X months.

        Args:
            origin_region: Region to forecast
            months_ahead: Number of months to forecast

        Returns:
            Dictionary with forecast data
        """
        # Get historical data for the region
        stmt = (
            select(CoffeePriceHistory)
            .where(CoffeePriceHistory.origin_region == origin_region)
            .order_by(CoffeePriceHistory.date.desc())
            .limit(100)
        )
        result = self.db.execute(stmt)
        historical = result.scalars().all()

        if not historical:
            return {
                "origin_region": origin_region,
                "forecast_data": [],
                "trend": "no_data",
            }

        # Simple trend-based forecast
        recent_prices = [h.price_usd_per_kg for h in historical[:12]]
        avg_price = sum(recent_prices) / len(recent_prices)

        # Calculate monthly growth rate
        if len(recent_prices) >= 2:
            growth_rate = (
                (recent_prices[0] - recent_prices[-1])
                / recent_prices[-1]
                / len(recent_prices)
            )
        else:
            growth_rate = 0.0

        forecast_data = []
        current_date = date.today()
        for i in range(months_ahead):
            forecast_month = (current_date.month + i) % 12 + 1
            forecast_year = current_date.year + (current_date.month + i) // 12
            forecast_price = avg_price * (1 + growth_rate * (i + 1))

            forecast_data.append(
                {
                    "month": f"{forecast_year}-{forecast_month:02d}",
                    "predicted_price": round(forecast_price, 2),
                    "confidence": max(0.3, 0.9 - i * 0.1),  # Decreasing confidence
                }
            )

        # Determine overall trend
        if growth_rate > 0.02:
            trend = "increasing"
        elif growth_rate < -0.02:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "origin_region": origin_region,
            "forecast_data": forecast_data,
            "trend": trend,
        }

    async def calculate_optimal_purchase_timing(
        self, origin_region: str, target_price_usd_per_kg: float
    ) -> dict[str, Any]:
        """Suggest optimal timing for purchase based on predicted trends.

        Args:
            origin_region: Region to analyze
            target_price_usd_per_kg: Target price threshold

        Returns:
            Dictionary with timing recommendations
        """
        # Get forecast
        forecast = await self.forecast_price_trend(origin_region, months_ahead=12)

        if not forecast["forecast_data"]:
            return {
                "origin_region": origin_region,
                "target_price": target_price_usd_per_kg,
                "recommendation": "no_data",
                "best_months": [],
            }

        # Find months where price is below target
        good_months = [
            month_data
            for month_data in forecast["forecast_data"]
            if month_data["predicted_price"] <= target_price_usd_per_kg
        ]

        if good_months:
            recommendation = "purchase_recommended"
            best_months = [m["month"] for m in good_months[:3]]
        else:
            # Find lowest price months
            sorted_months = sorted(
                forecast["forecast_data"], key=lambda x: x["predicted_price"]
            )
            recommendation = "wait_for_best_timing"
            best_months = [m["month"] for m in sorted_months[:3]]

        return {
            "origin_region": origin_region,
            "target_price": target_price_usd_per_kg,
            "recommendation": recommendation,
            "best_months": best_months,
            "forecast_trend": forecast["trend"],
        }

    def train_model(self, training_data: pd.DataFrame) -> dict[str, Any]:
        """Train coffee price prediction model.

        Args:
            training_data: DataFrame with historical price data

        Returns:
            Dictionary with training results
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
