"""Tests for outreach API routes."""

from app.models.cooperative import Cooperative
from app.models.roaster import Roaster


def test_generate_outreach_for_cooperative(client, auth_headers, db):
    """Test generating outreach for a cooperative."""
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()
    db.refresh(coop)

    payload = {
        "entity_type": "cooperative",
        "entity_id": coop.id,
        "language": "en",
        "purpose": "sourcing_pitch",
        "refine_with_llm": False,
    }

    response = client.post("/outreach/generate", json=payload, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "text" in data


def test_generate_outreach_for_roaster(client, auth_headers, db):
    """Test generating outreach for a roaster."""
    roaster = Roaster(name="Test Roaster", city="Berlin")
    db.add(roaster)
    db.commit()
    db.refresh(roaster)

    payload = {
        "entity_type": "roaster",
        "entity_id": roaster.id,
        "language": "de",
        "purpose": "sourcing_pitch",
        "refine_with_llm": False,
    }

    response = client.post("/outreach/generate", json=payload, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_generate_outreach_invalid_entity_type(client, auth_headers, db):
    """Test generating outreach with invalid entity type."""
    payload = {
        "entity_type": "invalid",
        "entity_id": 1,
        "language": "en",
        "purpose": "sourcing_pitch",
        "refine_with_llm": False,
    }

    response = client.post("/outreach/generate", json=payload, headers=auth_headers)

    assert response.status_code == 400


def test_generate_outreach_entity_not_found(client, auth_headers, db):
    """Test generating outreach for non-existent entity."""
    payload = {
        "entity_type": "cooperative",
        "entity_id": 99999,
        "language": "en",
        "purpose": "sourcing_pitch",
        "refine_with_llm": False,
    }

    response = client.post("/outreach/generate", json=payload, headers=auth_headers)

    assert response.status_code == 400


def test_generate_outreach_viewer_can_access(client, viewer_auth_headers, db):
    """Test that viewers can generate outreach."""
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()
    db.refresh(coop)

    payload = {
        "entity_type": "cooperative",
        "entity_id": coop.id,
        "language": "en",
        "purpose": "sourcing_pitch",
        "refine_with_llm": False,
    }

    response = client.post(
        "/outreach/generate", json=payload, headers=viewer_auth_headers
    )

    assert response.status_code == 200


def test_generate_outreach_without_auth(client, db):
    """Test generating outreach without authentication."""
    payload = {
        "entity_type": "cooperative",
        "entity_id": 1,
        "language": "en",
        "purpose": "sourcing_pitch",
        "refine_with_llm": False,
    }

    response = client.post("/outreach/generate", json=payload)

    assert response.status_code == 401


def test_generate_outreach_different_languages(client, auth_headers, db):
    """Test generating outreach in different languages."""
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()
    db.refresh(coop)

    languages = ["en", "de", "es"]

    for lang in languages:
        payload = {
            "entity_type": "cooperative",
            "entity_id": coop.id,
            "language": lang,
            "purpose": "sourcing_pitch",
            "refine_with_llm": False,
        }

        response = client.post("/outreach/generate", json=payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == lang
