"""Data freshness monitoring service.

Tracks staleness across all data sources and provides freshness reports.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

import structlog
from sqlalchemy.orm import Session

log = structlog.get_logger()


class DataFreshnessMonitor:
    """Track data staleness across all sources."""

    def __init__(self, db: Session):
        """Initialize freshness monitor.

        Args:
            db: Database session
        """
        self.db = db

    def _get_latest_observation(self, key: str) -> Optional[dict]:
        """Get latest observation for a key.

        Args:
            key: Market observation key (e.g., "FX:USD_EUR")

        Returns:
            Dictionary with timestamp and age info, or None
        """
        from app.models.market import MarketObservation

        obs = (
            self.db.query(MarketObservation)
            .filter(MarketObservation.key == key)
            .order_by(MarketObservation.observed_at.desc())
            .first()
        )

        if not obs:
            return None

        now = datetime.now(timezone.utc)
        age_delta = now - obs.observed_at
        age_hours = age_delta.total_seconds() / 3600

        return {
            "last_updated": obs.observed_at.isoformat(),
            "age_hours": round(age_hours, 2),
            "value": obs.value,
            "source": None,  # TODO: Add relationship or query separately
        }

    def _check_staleness(self, data: Optional[dict], max_age_hours: float) -> dict:
        """Check if data is stale.

        Args:
            data: Data dictionary with age_hours
            max_age_hours: Maximum acceptable age

        Returns:
            Dictionary with stale flag and status
        """
        if not data:
            return {
                "status": "missing",
                "stale": True,
                "reason": "No data available",
            }

        age_hours = data.get("age_hours", 999)
        if age_hours > max_age_hours:
            return {
                "status": "stale",
                "stale": True,
                "reason": f"Data is {age_hours:.1f}h old (max: {max_age_hours}h)",
            }

        return {
            "status": "fresh",
            "stale": False,
        }

    def get_freshness_report(self) -> dict:
        """Return staleness status for each data category.

        Returns:
            Dictionary with freshness status for all data sources
        """
        from app.models.news import NewsItem

        now = datetime.now(timezone.utc)

        # FX rates (expected to update daily)
        fx_data = self._get_latest_observation("FX:USD_EUR")
        fx_status = self._check_staleness(fx_data, max_age_hours=48)

        # Coffee prices (expected to update daily)
        coffee_data = self._get_latest_observation("COFFEE_C:USD_LB")
        coffee_status = self._check_staleness(coffee_data, max_age_hours=48)

        # Freight rates (expected to update weekly)
        freight_data = self._get_latest_observation("FREIGHT:CALLAO_HAMBURG")
        freight_status = self._check_staleness(freight_data, max_age_hours=168)

        # News (expected to update frequently)
        latest_news = (
            self.db.query(NewsItem).order_by(NewsItem.published_at.desc()).first()
        )

        if latest_news:
            age_delta = now - latest_news.published_at
            age_hours = age_delta.total_seconds() / 3600
            news_data = {
                "last_updated": latest_news.published_at.isoformat(),
                "age_hours": round(age_hours, 2),
                "title": latest_news.title[:100] if latest_news.title else None,
            }
            news_status = self._check_staleness(news_data, max_age_hours=48)
        else:
            news_data = None
            news_status = {
                "status": "missing",
                "stale": True,
                "reason": "No news items available",
            }

        # Peru weather (expected to update daily)
        weather_keys = [
            "WEATHER:PERU_CAJAMARCA",
            "WEATHER:PERU_JUNIN",
            "WEATHER:PERU_SAN_MARTIN",
        ]
        weather_data = {}
        for key in weather_keys:
            region = key.split(":")[-1].replace("_", " ").title()
            obs_data = self._get_latest_observation(key)
            status = self._check_staleness(obs_data, max_age_hours=48)
            weather_data[region] = {
                **(obs_data or {}),
                **status,
            }

        return {
            "timestamp": now.isoformat(),
            "overall_status": (
                "healthy"
                if not (
                    fx_status["stale"] or coffee_status["stale"] or news_status["stale"]
                )
                else "degraded"
            ),
            "categories": {
                "fx_rates": {
                    "USD_EUR": {
                        **(fx_data or {}),
                        **fx_status,
                    }
                },
                "coffee_prices": {
                    "COFFEE_C": {
                        **(coffee_data or {}),
                        **coffee_status,
                    }
                },
                "freight_rates": {
                    "CALLAO_HAMBURG": {
                        **(freight_data or {}),
                        **freight_status,
                    }
                },
                "news": {
                    "latest": {
                        **(news_data or {}),
                        **news_status,
                    }
                },
                "weather": weather_data,
            },
        }

    def get_stale_entities(self, entity_type: str, stale_days: int) -> list:
        """Get entities that haven't been updated recently.

        Args:
            entity_type: Type of entity ("cooperative" or "roaster")
            stale_days: Number of days before considering stale

        Returns:
            List of entity IDs that need refreshing
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=stale_days)

        if entity_type == "cooperative":
            from app.models.cooperative import Cooperative

            stale = (
                self.db.query(Cooperative.id)
                .filter(
                    (Cooperative.last_verified_at.is_(None))
                    | (Cooperative.last_verified_at < cutoff)
                )
                .order_by(Cooperative.last_verified_at.asc().nullsfirst())
                .limit(10)
                .all()
            )
        elif entity_type == "roaster":
            from app.models.roaster import Roaster

            stale = (
                self.db.query(Roaster.id)
                .filter(
                    (Roaster.last_verified_at.is_(None))
                    | (Roaster.last_verified_at < cutoff)
                )
                .order_by(Roaster.last_verified_at.asc().nullsfirst())
                .limit(10)
                .all()
            )
        else:
            return []

        return [entity_id for (entity_id,) in stale]
