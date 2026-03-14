from datetime import datetime, timezone

from app.models.market import MarketObservation
from app.models.news_item import NewsItem


def test_monitoring_dashboard_endpoint(client, auth_headers, db):
    db.add(
        MarketObservation(
            key="FX:USD_EUR",
            value=0.93,
            observed_at=datetime.now(timezone.utc),
        )
    )
    db.add(
        NewsItem(
            topic="market",
            title="Market intelligence update",
            url="https://example.com/market-intelligence",
            published_at=datetime.now(timezone.utc),
            retrieved_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    response = client.get("/monitoring/dashboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "pipeline_health" in data
    assert "schedule_status" in data
    assert data["provider_summary"]["total_sources"] >= 1
    assert "phase4_health" in data


def test_monitoring_sources_and_schedules_endpoints(client, auth_headers):
    sources = client.get("/monitoring/sources", headers=auth_headers)
    assert sources.status_code == 200
    assert "sources" in sources.json()
    assert "provider_catalog" in sources.json()

    schedules = client.get("/monitoring/schedules", headers=auth_headers)
    assert schedules.status_code == 200
    assert schedules.json()["total"] >= 1
    assert "summary" in schedules.json()
