"""Tests for dedup API routes."""

from app.models.cooperative import Cooperative
from app.models.roaster import Roaster


def test_suggest_duplicates_cooperatives(client, auth_headers, db):
    """Test suggesting duplicate cooperatives."""
    coop1 = Cooperative(name="Coffee Cooperative", region="Cajamarca")
    coop2 = Cooperative(name="Coffee Coop", region="Cajamarca")
    db.add_all([coop1, coop2])
    db.commit()

    response = client.get(
        "/dedup/suggest?entity_type=cooperative&threshold=80", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_suggest_duplicates_roasters(client, auth_headers, db):
    """Test suggesting duplicate roasters."""
    roaster1 = Roaster(name="Berlin Coffee Roasters", city="Berlin")
    roaster2 = Roaster(name="Berlin Coffee", city="Berlin")
    db.add_all([roaster1, roaster2])
    db.commit()

    response = client.get(
        "/dedup/suggest?entity_type=roaster&threshold=80", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_suggest_duplicates_invalid_entity_type(client, auth_headers, db):
    """Test suggesting duplicates with invalid entity type."""
    response = client.get("/dedup/suggest?entity_type=invalid", headers=auth_headers)

    assert response.status_code == 400


def test_suggest_duplicates_empty_database(client, auth_headers, db):
    """Test suggesting duplicates with empty database."""
    response = client.get(
        "/dedup/suggest?entity_type=cooperative", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_suggest_duplicates_with_custom_threshold(client, auth_headers, db):
    """Test suggesting duplicates with custom threshold."""
    coop1 = Cooperative(name="ABC Coffee", region="Cajamarca")
    coop2 = Cooperative(name="XYZ Coffee", region="Junin")
    db.add_all([coop1, coop2])
    db.commit()

    response = client.get(
        "/dedup/suggest?entity_type=cooperative&threshold=50", headers=auth_headers
    )

    assert response.status_code == 200


def test_suggest_duplicates_unauthorized(client, viewer_auth_headers, db):
    """Test that viewers cannot suggest duplicates."""
    response = client.get(
        "/dedup/suggest?entity_type=cooperative", headers=viewer_auth_headers
    )

    assert response.status_code == 403


def test_suggest_duplicates_without_auth(client, db):
    """Test suggesting duplicates without authentication."""
    response = client.get("/dedup/suggest?entity_type=cooperative")

    assert response.status_code == 401


def test_suggest_duplicates_with_limit(client, auth_headers, db):
    """Test suggesting duplicates with limit parameter."""
    for i in range(10):
        coop = Cooperative(name=f"Coffee {i}", region="Cajamarca")
        db.add(coop)
    db.commit()

    response = client.get(
        "/dedup/suggest?entity_type=cooperative&threshold=50&limit=5",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5
