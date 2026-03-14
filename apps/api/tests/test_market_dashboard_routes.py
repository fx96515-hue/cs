from datetime import datetime, timezone

from app.models.cooperative import Cooperative
from app.models.market import MarketObservation
from app.models.news_item import NewsItem


def test_market_latest_snapshot_endpoint(client, auth_headers, db):
    db.add_all(
        [
            MarketObservation(
                key="FX:USD_EUR",
                value=0.92,
                observed_at=datetime.now(timezone.utc),
            ),
            MarketObservation(
                key="COFFEE_C:USD_LB",
                value=2.45,
                unit="lb",
                currency="USD",
                observed_at=datetime.now(timezone.utc),
            ),
        ]
    )
    db.commit()

    response = client.get("/market/latest", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["FX:USD_EUR"]["value"] == 0.92
    assert data["COFFEE_C:USD_LB"]["currency"] == "USD"


def test_market_series_and_realtime_status_endpoints(client, auth_headers, db):
    db.add(
        MarketObservation(
            key="COFFEE_C:USD_LB",
            value=2.51,
            unit="lb",
            currency="USD",
            observed_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    series_response = client.get(
        "/market/series?key=COFFEE_C:USD_LB&limit=30", headers=auth_headers
    )
    assert series_response.status_code == 200
    assert len(series_response.json()) == 1

    realtime_response = client.get("/market/realtime/status", headers=auth_headers)
    assert realtime_response.status_code == 200
    assert "realtime_enabled" in realtime_response.json()


def test_news_and_cooperatives_endpoints_for_markt_page(client, auth_headers, db):
    db.add(
        NewsItem(
            topic="peru coffee",
            title="Peru export report",
            url="https://example.com/peru-export-report",
            snippet="Exports are up this quarter.",
            published_at=datetime.now(timezone.utc),
            retrieved_at=datetime.now(timezone.utc),
        )
    )
    db.add(
        Cooperative(
            name="Coop Norte",
            region="Cajamarca",
            certifications="Organic, Fair Trade",
            status="active",
            total_score=87.4,
        )
    )
    db.commit()

    news_response = client.get(
        "/news?topic=peru%20coffee&limit=8&days=14", headers=auth_headers
    )
    assert news_response.status_code == 200
    assert news_response.json()[0]["title"] == "Peru export report"

    coops_response = client.get("/cooperatives", headers=auth_headers)
    assert coops_response.status_code == 200
    assert coops_response.json()[0]["region"] == "Cajamarca"
