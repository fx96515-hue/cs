from datetime import datetime, timezone

from app.models.market import MarketObservation
from app.models.source import Source
from app.services.data_pipeline.freshness import DataFreshnessMonitor


def test_latest_observation_resolves_source_name(db):
    source = Source(name="ECB Feed", url="https://example.com/fx", kind="api")
    db.add(source)
    db.commit()
    db.refresh(source)

    db.add(
        MarketObservation(
            key="FX:USD_EUR",
            value=0.92,
            unit=None,
            currency=None,
            observed_at=datetime.now(timezone.utc),
            source_id=source.id,
        )
    )
    db.commit()

    monitor = DataFreshnessMonitor(db)
    result = monitor._get_latest_observation("FX:USD_EUR")

    assert result is not None
    assert result["source"] == "ECB Feed"


def test_latest_observation_without_source_stays_none(db):
    db.add(
        MarketObservation(
            key="COFFEE_C:USD_LB",
            value=2.45,
            unit="lb",
            currency="USD",
            observed_at=datetime.now(timezone.utc),
            source_id=None,
        )
    )
    db.commit()

    monitor = DataFreshnessMonitor(db)
    result = monitor._get_latest_observation("COFFEE_C:USD_LB")

    assert result is not None
    assert result["source"] is None
