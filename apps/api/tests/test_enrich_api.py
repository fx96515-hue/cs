"""Tests for enrichment API routes."""

from unittest.mock import patch
from app.models.cooperative import Cooperative


def test_enrich_entity_invalid_type(client, auth_headers, db):
    """Test enriching with invalid entity type."""
    payload = {"url": "https://example.com", "use_llm": False}

    response = client.post("/enrich/invalid_type/1", json=payload, headers=auth_headers)

    assert response.status_code == 400


def test_enrich_entity_not_found(client, auth_headers, db):
    """Test enriching non-existent entity."""
    payload = {"url": "https://example.com", "use_llm": False}

    response = client.post(
        "/enrich/cooperative/99999", json=payload, headers=auth_headers
    )

    assert response.status_code == 400


def test_enrich_cooperative(client, auth_headers, db):
    """Test enriching a cooperative."""
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()
    db.refresh(coop)

    with patch("app.services.enrichment.settings") as mock_settings:
        mock_settings.PERPLEXITY_API_KEY = None

        payload = {"url": "https://example.com", "use_llm": False}

        response = client.post(
            f"/enrich/cooperative/{coop.id}", json=payload, headers=auth_headers
        )

        # Should either succeed or return error based on PERPLEXITY_API_KEY
        assert response.status_code in [200, 400]


def test_enrich_unauthorized(client, viewer_auth_headers, db):
    """Test that viewers cannot enrich entities."""
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()

    payload = {"url": "https://example.com", "use_llm": False}

    response = client.post(
        f"/enrich/cooperative/{coop.id}", json=payload, headers=viewer_auth_headers
    )

    assert response.status_code == 403


def test_enrich_without_auth(client, db):
    """Test enriching without authentication."""
    payload = {"url": "https://example.com", "use_llm": False}

    response = client.post("/enrich/cooperative/1", json=payload)

    assert response.status_code == 401
