"""Optimal purchase timing analysis for coffee sourcing."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Literal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.coffee_price_history import CoffeePriceHistory
import pandas as pd
import numpy as np


PurchaseRecommendation = Literal["buy_now", "wait", "monitor_closely"]


def analyze_price_trends(
    db: Session, *, origin_region: str | None = None, days_lookback: int = 180
) -> dict[str, Any]:
    """Analyze historical price trends.

    Args:
        db: Database session
        origin_region: Optional region filter
        days_lookback: Days of history to analyze

    Returns:
        Price trend analysis
    """
    # Get historical data
    cutoff_date = datetime.now() - timedelta(days=days_lookback)
    stmt = select(CoffeePriceHistory).where(CoffeePriceHistory.date >= cutoff_date)

    if origin_region:
        stmt = stmt.where(CoffeePriceHistory.origin_region == origin_region)

    stmt = stmt.order_by(CoffeePriceHistory.date)
    result = db.execute(stmt)
    records = result.scalars().all()

    if not records:
        return {
            "status": "insufficient_data",
            "message": "Not enough historical data for analysis",
        }

    # Convert to DataFrame
    df = pd.DataFrame(
        [
            {
                "date": r.date,
                "price": r.price_usd_per_kg,
                "ice_c_price": r.ice_c_price_usd_per_lb,
            }
            for r in records
        ]
    )

    # Calculate statistics
    current_price = df["price"].iloc[-1] if len(df) > 0 else 0
    avg_price = df["price"].mean()
    min_price = df["price"].min()
    max_price = df["price"].max()
    std_price = df["price"].std()

    # Calculate trend (simple linear regression)
    if len(df) > 1:
        x = np.arange(len(df))
        # Ensure numeric numpy array for mypy/type-safety
        slope = np.polyfit(x, df["price"].to_numpy(dtype=float), 1)[0]
        trend = (
            "increasing"
            if slope > 0.01
            else "decreasing"
            if slope < -0.01
            else "stable"
        )
    else:
        trend = "unknown"
        slope = 0.0

    # Price volatility
    volatility = std_price / avg_price if avg_price > 0 else 0

    return {
        "status": "ok",
        "current_price": float(current_price),
        "average_price": float(avg_price),
        "min_price": float(min_price),
        "max_price": float(max_price),
        "std_deviation": float(std_price),
        "volatility": float(volatility),
        "trend": trend,
        "trend_slope": float(slope),
        "samples": len(df),
    }


def get_seasonal_patterns(
    db: Session, *, origin_region: str | None = None
) -> dict[str, Any]:
    """Analyze seasonal price patterns.

    Peru harvest calendar:
    - Main harvest: April - September
    - Fly crop: October - December

    Args:
        db: Database session
        origin_region: Optional region filter

    Returns:
        Seasonal analysis
    """
    # Get all historical data
    stmt = select(CoffeePriceHistory)

    if origin_region:
        stmt = stmt.where(CoffeePriceHistory.origin_region == origin_region)

    result = db.execute(stmt)
    records = result.scalars().all()

    if not records:
        return {
            "status": "insufficient_data",
            "message": "Not enough data for seasonal analysis",
        }

    # Group by month
    monthly_prices: dict[int, list[float]] = {i: [] for i in range(1, 13)}
    for record in records:
        # record.date is SQLAlchemy Date type which has .month attribute at runtime
        month = getattr(record.date, "month")
        monthly_prices[month].append(record.price_usd_per_kg)

    # Calculate average by month
    monthly_avg = {
        month: float(np.mean(prices)) if prices else 0.0
        for month, prices in monthly_prices.items()
    }

    # Identify best buying months (lowest prices)
    sorted_months = sorted(monthly_avg.items(), key=lambda x: x[1])
    best_months = [m for m, _ in sorted_months[:3] if monthly_avg[m] > 0]

    return {
        "status": "ok",
        "monthly_averages": monthly_avg,
        "best_buying_months": best_months,
        "harvest_calendar": {
            "main_harvest": "April-September",
            "fly_crop": "October-December",
        },
    }


def get_purchase_timing_recommendation(
    db: Session,
    *,
    origin_region: str | None = None,
    target_quantity_kg: float | None = None,
) -> dict[str, Any]:
    """Get optimal purchase timing recommendation.

    Args:
        db: Database session
        origin_region: Optional region filter
        target_quantity_kg: Target purchase quantity

    Returns:
        Purchase timing recommendation with confidence score
    """
    # Analyze trends
    trends = analyze_price_trends(db, origin_region=origin_region, days_lookback=180)

    if trends["status"] != "ok":
        return {
            "recommendation": "monitor_closely",
            "confidence": 0.3,
            "reason": "Insufficient data for recommendation",
            "details": trends,
        }

    # Analyze seasonality
    seasonal = get_seasonal_patterns(db, origin_region=origin_region)

    current_month = datetime.now().month
    current_price = trends["current_price"]
    avg_price = trends["average_price"]
    trend = trends["trend"]
    volatility = trends["volatility"]

    # Decision logic
    recommendation: PurchaseRecommendation
    reason = ""

    # Price below average and stable/decreasing trend
    if current_price < avg_price * 0.95 and trend in ["stable", "decreasing"]:
        recommendation = "buy_now"
        confidence = 0.85
        reason = f"Price is {((avg_price - current_price) / avg_price * 100):.1f}% below average and {trend}"

    # Price increasing but in good buying season
    elif trend == "increasing" and seasonal["status"] == "ok":
        best_months = seasonal.get("best_buying_months", [])
        if current_month in best_months:
            recommendation = "buy_now"
            confidence = 0.75
            reason = f"Currently in favorable buying season (month {current_month})"
        else:
            recommendation = "wait"
            confidence = 0.70
            reason = (
                f"Prices increasing, wait for better season. Best months: {best_months}"
            )

    # Price above average and increasing
    elif current_price > avg_price * 1.05 and trend == "increasing":
        recommendation = "wait"
        confidence = 0.80
        reason = f"Price is {((current_price - avg_price) / avg_price * 100):.1f}% above average and increasing"

    # High volatility
    elif volatility > 0.15:
        recommendation = "monitor_closely"
        confidence = 0.60
        reason = f"High price volatility ({volatility:.2%}), market unstable"

    # Default: monitor
    else:
        recommendation = "monitor_closely"
        confidence = 0.55
        reason = "Market conditions unclear, continue monitoring"

    # Peru-specific harvest timing
    if origin_region and "peru" in origin_region.lower():
        # Main harvest months (Apr-Sep) usually have better availability/prices
        if 4 <= current_month <= 9:
            if recommendation == "monitor_closely":
                recommendation = "buy_now"
                confidence = min(confidence + 0.15, 0.95)
                reason += " (Peru main harvest season)"

    return {
        "recommendation": recommendation,
        "confidence": float(confidence),
        "reason": reason,
        "current_price": float(current_price),
        "average_price": float(avg_price),
        "trend": trend,
        "volatility": float(volatility),
        "current_month": current_month,
        "details": {
            "price_analysis": trends,
            "seasonal_analysis": seasonal,
        },
    }


def get_price_forecast(
    db: Session, *, origin_region: str | None = None, days_ahead: int = 30
) -> dict[str, Any]:
    """Generate simple price forecast.

    Args:
        db: Database session
        origin_region: Optional region filter
        days_ahead: Days to forecast

    Returns:
        Price forecast
    """
    # Get recent trends
    trends = analyze_price_trends(db, origin_region=origin_region, days_lookback=90)

    if trends["status"] != "ok":
        return {
            "status": "insufficient_data",
            "message": "Not enough data for forecasting",
        }

    # Simple linear extrapolation
    current_price = trends["current_price"]
    daily_change = trends["trend_slope"] / 90  # Approximate daily change

    forecast_dates = [datetime.now() + timedelta(days=i) for i in range(days_ahead)]
    forecast_prices = [
        float(max(0, current_price + (daily_change * i))) for i in range(days_ahead)
    ]

    # Confidence decreases with time
    confidence = [
        float(max(0.3, 0.9 - (i / days_ahead) * 0.5)) for i in range(days_ahead)
    ]

    return {
        "status": "ok",
        "forecast_days": days_ahead,
        "current_price": float(current_price),
        "forecast": [
            {
                "date": date.isoformat(),
                "predicted_price": price,
                "confidence": conf,
            }
            for date, price, conf in zip(forecast_dates, forecast_prices, confidence)
        ],
        "trend": trends["trend"],
        "note": "Simple linear forecast - use with caution",
    }
