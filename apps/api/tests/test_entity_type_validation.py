"""Tests for entity type validation in API routes."""

from fastapi.testclient import TestClient
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster


def test_enrich_invalid_entity_type_rejected(client: TestClient, auth_headers):
    """Test that POST /enrich/invalid_entity/1 returns 400."""
    response = client.post(
        "/enrich/invalid_entity/1",
        json={"url": "https://example.com"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    # Manual validation should reject this


def test_enrich_cooperative_valid_type(client: TestClient, auth_headers, db):
    """Test that POST /enrich/cooperative/{id} accepts cooperative entity type."""
    # Create a cooperative first
    coop = Cooperative(
        name="Test Cooperative",
        region="Cajamarca",
        website="https://testcoop.com",
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    response = client.post(
        f"/enrich/cooperative/{coop.id}",
        json={"url": "https://testcoop.com"},
        headers=auth_headers,
    )
    # Should not be a validation error (422) for valid entity_type
    assert response.status_code != 422, (
        f"Valid entity_type 'cooperative' should not return 422: {response.json()}"
    )
    # Should be one of these expected status codes
    # Accept 409 Conflict as Perplexity/web_extract UNIQUE constraint can occur
    assert response.status_code in [200, 400, 404, 409, 503]  # 503 if no API key


def test_enrich_roaster_valid_type(client: TestClient, auth_headers, db):
    """Test that POST /enrich/roaster/{id} accepts roaster entity type."""
    # Create a roaster first
    roaster = Roaster(
        name="Test Roaster",
        city="Berlin",
        website="https://testroaster.com",
    )
    db.add(roaster)
    db.commit()
    db.refresh(roaster)

    response = client.post(
        f"/enrich/roaster/{roaster.id}",
        json={"url": "https://testroaster.com"},
        headers=auth_headers,
    )
    # Should not be a validation error (422) for valid entity_type
    assert response.status_code != 422, (
        f"Valid entity_type 'roaster' should not return 422: {response.json()}"
    )
    # Should be one of these expected status codes
    assert response.status_code in [200, 400, 404, 503]  # 503 if no API key


def test_auto_outreach_suggestions_invalid_entity_type(
    client: TestClient, auth_headers
):
    """Test that /auto-outreach/suggestions with invalid entity_type returns 422."""
    response = client.get(
        "/auto-outreach/suggestions?entity_type=invalid&limit=10",
        headers=auth_headers,
    )
    assert response.status_code == 422
    # Pydantic validation should reject this


def test_auto_outreach_suggestions_cooperative_valid(client: TestClient, auth_headers):
    """Test that /auto-outreach/suggestions accepts cooperative entity type."""
    response = client.get(
        "/auto-outreach/suggestions?entity_type=cooperative&limit=10",
        headers=auth_headers,
    )
    # Should not be a validation error (422) for valid entity_type
    assert response.status_code != 422, (
        f"Valid entity_type 'cooperative' should not return 422: {response.json()}"
    )
    # Should succeed (200) or fail with non-validation error
    assert response.status_code in [200, 500]


def test_auto_outreach_suggestions_roaster_valid(client: TestClient, auth_headers):
    """Test that /auto-outreach/suggestions accepts roaster entity type."""
    response = client.get(
        "/auto-outreach/suggestions?entity_type=roaster&limit=10",
        headers=auth_headers,
    )
    # Should not be a validation error (422) for valid entity_type
    assert response.status_code != 422, (
        f"Valid entity_type 'roaster' should not return 422: {response.json()}"
    )
    # Should succeed (200) or fail with non-validation error
    assert response.status_code in [200, 500]


def test_auto_outreach_status_invalid_entity_type(client: TestClient, auth_headers):
    """Test that /auto-outreach/status with invalid entity_type returns 422."""
    response = client.get(
        "/auto-outreach/status/invalid/1",
        headers=auth_headers,
    )
    assert response.status_code == 422
    # Pydantic validation should reject this


def test_auto_outreach_status_cooperative_valid(client: TestClient, auth_headers, db):
    """Test that /auto-outreach/status accepts cooperative entity type."""
    # Create a cooperative first
    coop = Cooperative(
        name="Test Cooperative",
        region="Cajamarca",
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    response = client.get(
        f"/auto-outreach/status/cooperative/{coop.id}",
        headers=auth_headers,
    )
    # Should not be a validation error (422) for valid entity_type
    assert response.status_code != 422, (
        f"Valid entity_type 'cooperative' should not return 422: {response.json()}"
    )
    # Should succeed (200) or fail with non-validation error
    assert response.status_code in [200, 500]


def test_auto_outreach_status_roaster_valid(client: TestClient, auth_headers, db):
    """Test that /auto-outreach/status accepts roaster entity type."""
    # Create a roaster first
    roaster = Roaster(
        name="Test Roaster",
        city="Berlin",
    )
    db.add(roaster)
    db.commit()
    db.refresh(roaster)

    response = client.get(
        f"/auto-outreach/status/roaster/{roaster.id}",
        headers=auth_headers,
    )
    # Should not be a validation error (422) for valid entity_type
    assert response.status_code != 422, (
        f"Valid entity_type 'roaster' should not return 422: {response.json()}"
    )
    # Should succeed (200) or fail with non-validation error
    assert response.status_code in [200, 500]


def test_campaign_create_invalid_entity_type(client: TestClient, auth_headers):
    """Test that creating campaign with invalid entity_type returns 422."""
    payload = {
        "name": "Test Campaign",
        "entity_type": "invalid",
        "language": "de",
        "purpose": "sourcing_pitch",
        "limit": 10,
    }
    response = client.post(
        "/auto-outreach/campaign",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 422
    # Pydantic validation should reject this


def test_campaign_create_cooperative_valid(client: TestClient, auth_headers):
    """Test that creating campaign with cooperative entity_type is accepted."""
    payload = {
        "name": "Test Campaign",
        "entity_type": "cooperative",
        "language": "de",
        "purpose": "sourcing_pitch",
        "limit": 10,
    }
    response = client.post(
        "/auto-outreach/campaign",
        json=payload,
        headers=auth_headers,
    )
    # Should not be a validation error (422) for valid entity_type
    assert response.status_code != 422, (
        f"Valid entity_type 'cooperative' should not return 422: {response.json()}"
    )
    # Should succeed (200) or fail with non-validation error
    assert response.status_code in [200, 400, 500]


def test_campaign_create_roaster_valid(client: TestClient, auth_headers):
    """Test that creating campaign with roaster entity_type is accepted."""
    payload = {
        "name": "Test Campaign",
        "entity_type": "roaster",
        "language": "de",
        "purpose": "sourcing_pitch",
        "limit": 10,
    }
    response = client.post(
        "/auto-outreach/campaign",
        json=payload,
        headers=auth_headers,
    )
    # Should not be a validation error (422) for valid entity_type
    assert response.status_code != 422, (
        f"Valid entity_type 'roaster' should not return 422: {response.json()}"
    )
    # Should succeed (200) or fail with non-validation error
    assert response.status_code in [200, 400, 500]
