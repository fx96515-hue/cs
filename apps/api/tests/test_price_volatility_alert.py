"""Tests for the price volatility quality alert."""

from datetime import datetime, timedelta, timezone

import pytest

from app.models.market import MarketObservation
from app.models.quality_alert import QualityAlert
from app.services.quality_alerts import detect_price_volatility


def _add_obs(db, value: float, minutes_ago: int) -> MarketObservation:
    obs = MarketObservation(
        key="COFFEE_C:USD_LB",
        value=value,
        observed_at=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago),
    )
    db.add(obs)
    db.commit()
    return obs


class TestDetectPriceVolatility:
    def test_no_data_returns_empty(self, db):
        alerts = detect_price_volatility(db, threshold_pct=5.0)
        assert alerts == []

    def test_single_observation_returns_empty(self, db):
        _add_obs(db, 2.40, 60)
        alerts = detect_price_volatility(db, threshold_pct=5.0)
        assert alerts == []

    def test_below_threshold_returns_empty(self, db):
        _add_obs(db, 2.40, 120)
        _add_obs(db, 2.45, 10)  # ~2.1% change – below 5%
        alerts = detect_price_volatility(db, threshold_pct=5.0)
        assert alerts == []

    def test_above_threshold_creates_alert(self, db):
        _add_obs(db, 2.00, 120)
        _add_obs(db, 2.15, 10)  # +7.5% – above 5%
        alerts = detect_price_volatility(db, threshold_pct=5.0)

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.alert_type == "price_volatility"
        assert alert.entity_type == "market"
        assert alert.field_name == "COFFEE_C:USD_LB"
        assert alert.old_value == pytest.approx(2.00)
        assert alert.new_value == pytest.approx(2.15)
        assert alert.change_amount == pytest.approx(7.5)
        assert alert.acknowledged is False

    def test_drop_above_threshold_creates_alert(self, db):
        _add_obs(db, 2.40, 120)
        _add_obs(db, 2.20, 10)  # -8.3% – above 5%
        alerts = detect_price_volatility(db, threshold_pct=5.0)

        assert len(alerts) == 1
        val = alerts[0].change_amount
        assert val is not None
        assert val < 0

    def test_severity_info_for_small_swing(self, db):
        _add_obs(db, 2.00, 120)
        _add_obs(db, 2.12, 10)  # +6% – info severity
        alerts = detect_price_volatility(db, threshold_pct=5.0)

        assert len(alerts) == 1
        assert alerts[0].severity == "info"

    def test_severity_warning_for_medium_swing(self, db):
        _add_obs(db, 2.00, 120)
        _add_obs(db, 2.16, 10)  # +8% – warning severity
        alerts = detect_price_volatility(db, threshold_pct=5.0)

        assert len(alerts) == 1
        assert alerts[0].severity == "warning"

    def test_severity_critical_for_large_swing(self, db):
        _add_obs(db, 2.00, 120)
        _add_obs(db, 2.25, 10)  # +12.5% – critical severity
        alerts = detect_price_volatility(db, threshold_pct=5.0)

        assert len(alerts) == 1
        assert alerts[0].severity == "critical"

    def test_alert_persisted_to_database(self, db):
        _add_obs(db, 2.00, 120)
        _add_obs(db, 2.15, 10)
        detect_price_volatility(db, threshold_pct=5.0)

        saved = (
            db.query(QualityAlert)
            .filter(QualityAlert.alert_type == "price_volatility")
            .first()
        )
        assert saved is not None
        assert saved.entity_type == "market"
