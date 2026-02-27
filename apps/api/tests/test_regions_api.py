"""Tests for regions API routes."""

from app.models.peru_region import PeruRegion


def test_list_peru_regions_empty(client, auth_headers, db):
    """Test listing Peru regions when none exist."""
    response = client.get("/regions/peru", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_peru_regions_with_data(client, auth_headers, db):
    """Test listing Peru regions with existing data."""
    region1 = PeruRegion(name="Cajamarca", code="CAJ")
    region2 = PeruRegion(name="Junin", code="JUN")
    db.add_all([region1, region2])
    db.commit()

    response = client.get("/regions/peru", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_seed_peru_regions(client, auth_headers, db):
    """Test seeding Peru regions."""
    response = client.post("/regions/peru/seed", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_seed_peru_regions_idempotent(client, auth_headers, db):
    """Test that seeding is idempotent."""
    # First seed
    response1 = client.post("/regions/peru/seed", headers=auth_headers)
    assert response1.status_code == 200

    # Second seed
    response2 = client.post("/regions/peru/seed", headers=auth_headers)
    assert response2.status_code == 200


def test_seed_unauthorized(client, viewer_auth_headers, db):
    """Test that viewers cannot seed regions."""
    response = client.post("/regions/peru/seed", headers=viewer_auth_headers)

    assert response.status_code == 403


def test_viewer_can_read_regions(client, viewer_auth_headers, db):
    """Test that viewers can read regions."""
    region = PeruRegion(name="Cajamarca", code="CAJ")
    db.add(region)
    db.commit()

    response = client.get("/regions/peru", headers=viewer_auth_headers)

    assert response.status_code == 200


def test_regions_without_auth(client, db):
    """Test accessing regions without authentication."""
    response = client.get("/regions/peru")

    assert response.status_code == 401
