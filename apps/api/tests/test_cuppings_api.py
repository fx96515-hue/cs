"""Tests for cuppings API routes."""

from app.models.cupping import CuppingResult
from datetime import datetime, timezone


def test_list_cuppings_empty(client, auth_headers, db):
    """Test listing cuppings when none exist."""
    response = client.get("/cuppings", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_create_cupping(client, auth_headers, db):
    """Test creating a cupping result."""
    payload = {"sca_score": 85.5, "occurred_at": datetime.now(timezone.utc).isoformat()}

    response = client.post("/cuppings", json=payload, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["sca_score"] == 85.5


def test_list_cuppings_with_data(client, auth_headers, db):
    """Test listing cuppings with existing data."""
    cupping1 = CuppingResult(sca_score=85.0, occurred_at=datetime.now(timezone.utc))
    cupping2 = CuppingResult(sca_score=87.0, occurred_at=datetime.now(timezone.utc))
    db.add_all([cupping1, cupping2])
    db.commit()

    response = client.get("/cuppings", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_create_cupping_unauthorized(client, viewer_auth_headers, db):
    """Test that viewers cannot create cuppings."""
    payload = {"sca_score": 85.5, "occurred_at": datetime.now(timezone.utc).isoformat()}

    response = client.post("/cuppings", json=payload, headers=viewer_auth_headers)

    assert response.status_code == 403


def test_viewer_can_read_cuppings(client, viewer_auth_headers, db):
    """Test that viewers can read cuppings."""
    cupping = CuppingResult(sca_score=85.0, occurred_at=datetime.now(timezone.utc))
    db.add(cupping)
    db.commit()

    response = client.get("/cuppings", headers=viewer_auth_headers)

    assert response.status_code == 200


def test_cuppings_without_auth(client, db):
    """Test accessing cuppings without authentication."""
    response = client.get("/cuppings")

    assert response.status_code == 401


def test_list_cuppings_with_limit(client, auth_headers, db):
    """Test listing cuppings with limit parameter."""
    for i in range(5):
        cupping = CuppingResult(
            sca_score=80.0 + i, occurred_at=datetime.now(timezone.utc)
        )
        db.add(cupping)
    db.commit()

    response = client.get("/cuppings?limit=3", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 3
