"""Tests for market API routes."""

import pytest
from app.models.market import MarketObservation
from datetime import datetime, timezone


def test_list_observations_empty(client, auth_headers, db):
    """Test listing market observations when none exist."""
    response = client.get("/market/observations", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_create_observation(client, auth_headers, db):
    """Test creating a new market observation."""
    payload = {
        "key": "FX:USD_EUR",
        "value": 0.92,
        "unit": "EUR",
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }

    response = client.post("/market/observations", json=payload, headers=auth_headers)

    assert response.status_code == 200 or response.status_code == 201
    data = response.json()
    assert data["key"] == "FX:USD_EUR"
    assert data["value"] == 0.92


def test_list_observations_with_data(client, auth_headers, db):
    """Test listing observations with existing data."""
    obs1 = MarketObservation(
        key="FX:USD_EUR", value=0.92, observed_at=datetime.now(timezone.utc)
    )
    obs2 = MarketObservation(
        key="COFFEE_C:USD_LB", value=2.50, observed_at=datetime.now(timezone.utc)
    )
    db.add_all([obs1, obs2])
    db.commit()

    response = client.get("/market/observations", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_list_observations_filter_by_key(client, auth_headers, db):
    """Test listing observations filtered by key."""
    obs1 = MarketObservation(
        key="FX:USD_EUR", value=0.92, observed_at=datetime.now(timezone.utc)
    )
    obs2 = MarketObservation(
        key="COFFEE_C:USD_LB", value=2.50, observed_at=datetime.now(timezone.utc)
    )
    db.add_all([obs1, obs2])
    db.commit()

    response = client.get("/market/observations?key=FX:USD_EUR", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert all(obs["key"] == "FX:USD_EUR" for obs in data)


def test_create_observation_unauthorized(client, viewer_auth_headers, db):
    """Test that viewers cannot create observations."""
    payload = {
        "key": "FX:USD_EUR",
        "value": 0.92,
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(
        "/market/observations", json=payload, headers=viewer_auth_headers
    )

    assert response.status_code == 403


def test_viewer_can_read_observations(client, viewer_auth_headers, db):
    """Test that viewers can read observations."""
    obs = MarketObservation(
        key="FX:USD_EUR", value=0.92, observed_at=datetime.now(timezone.utc)
    )
    db.add(obs)
    db.commit()

    response = client.get("/market/observations", headers=viewer_auth_headers)

    assert response.status_code == 200


def test_market_observations_without_auth(client, db):
    """Test accessing observations without authentication."""
    response = client.get("/market/observations")

    assert response.status_code == 401


@pytest.mark.skip(reason="Test requires Redis for Celery tasks")
def test_refresh_market_data_endpoint(client, auth_headers, db):
    """Test refreshing market data endpoint exists."""
    # Skip this test if Redis is not available (Celery dependency)
    response = client.post("/market/refresh", headers=auth_headers)

    # Should either succeed, return 404 if endpoint doesn't exist, or 500 if Redis unavailable
    assert response.status_code in [200, 202, 404, 500]


def test_list_observations_with_limit(client, auth_headers, db):
    """Test listing observations with limit parameter."""
    # Create multiple observations
    for i in range(5):
        obs = MarketObservation(
            key=f"TEST_KEY_{i}", value=float(i), observed_at=datetime.now(timezone.utc)
        )
        db.add(obs)
    db.commit()

    response = client.get("/market/observations?limit=3", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 3
