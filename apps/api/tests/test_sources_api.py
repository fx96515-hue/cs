"""Tests for sources API routes."""

from app.models.source import Source


def test_list_sources_empty(client, auth_headers, db):
    """Test listing sources when none exist."""
    response = client.get("/sources", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_create_source(client, auth_headers, db):
    """Test creating a new source."""
    payload = {
        "name": "Test Source",
        "url": "https://testsource.com",
        "kind": "api",
        "reliability": 0.8,
    }

    response = client.post("/sources", json=payload, headers=auth_headers)

    assert response.status_code == 200 or response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Source"
    assert data["url"] == "https://testsource.com"


def test_list_sources_with_data(client, auth_headers, db):
    """Test listing sources with existing data."""
    source1 = Source(name="Source 1", url="https://source1.com", kind="api")
    source2 = Source(name="Source 2", url="https://source2.com", kind="web")
    db.add_all([source1, source2])
    db.commit()

    response = client.get("/sources", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_get_source_by_id(client, auth_headers, db):
    """Test getting a specific source by ID."""
    source = Source(name="Test Source", url="https://test.com", kind="api")
    db.add(source)
    db.commit()
    db.refresh(source)

    response = client.get(f"/sources/{source.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == source.id
    assert data["name"] == "Test Source"


def test_get_source_not_found(client, auth_headers, db):
    """Test getting a non-existent source."""
    response = client.get("/sources/99999", headers=auth_headers)

    assert response.status_code == 404


def test_update_source(client, auth_headers, db):
    """Test updating a source."""
    source = Source(
        name="Test Source", url="https://test.com", kind="api", reliability=0.7
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    update_payload = {"reliability": 0.9}
    response = client.patch(
        f"/sources/{source.id}", json=update_payload, headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reliability"] == 0.9


def test_delete_source(client, auth_headers, db):
    """Test deleting a source."""
    source = Source(name="Test Source", url="https://test.com", kind="api")
    db.add(source)
    db.commit()
    db.refresh(source)

    response = client.delete(f"/sources/{source.id}", headers=auth_headers)

    assert response.status_code == 200 or response.status_code == 204


def test_create_source_unauthorized(client, viewer_auth_headers, db):
    """Test that viewers cannot create sources."""
    payload = {"name": "Test Source", "url": "https://test.com", "kind": "api"}

    response = client.post("/sources", json=payload, headers=viewer_auth_headers)

    assert response.status_code == 403


def test_viewer_can_read_sources(client, viewer_auth_headers, db):
    """Test that viewers can read sources."""
    source = Source(name="Test Source", url="https://test.com", kind="api")
    db.add(source)
    db.commit()

    response = client.get("/sources", headers=viewer_auth_headers)

    assert response.status_code == 200


def test_sources_without_auth(client, db):
    """Test accessing sources without authentication."""
    response = client.get("/sources")

    assert response.status_code == 401
