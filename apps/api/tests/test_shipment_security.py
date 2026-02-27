"""Tests for XSS protection in shipment schemas."""

from fastapi.testclient import TestClient
from app.models.shipment import Shipment


def test_xss_in_origin_port_rejected(client: TestClient, auth_headers):
    """Test that XSS in origin_port is rejected."""
    payload = {
        "container_number": "CONT12345",
        "bill_of_lading": "BOL123456",
        "weight_kg": 18000,
        "container_type": "40ft",
        "origin_port": "Callao<script>alert('xss')</script>",
        "destination_port": "Hamburg",
    }
    response = client.post("/shipments", json=payload, headers=auth_headers)
    assert response.status_code in [400, 422]
    detail = response.json()["detail"]
    assert any("invalid characters" in str(err).lower() for err in detail), (
        f"Expected XSS error, got: {detail}"
    )


def test_xss_in_destination_port_rejected(client: TestClient, auth_headers):
    """Test that XSS in destination_port is rejected."""
    payload = {
        "container_number": "CONT12345",
        "bill_of_lading": "BOL123456",
        "weight_kg": 18000,
        "container_type": "40ft",
        "origin_port": "Callao",
        "destination_port": "Hamburg<iframe src='evil.com'></iframe>",
    }
    response = client.post("/shipments", json=payload, headers=auth_headers)
    assert response.status_code in [400, 422]
    detail = response.json()["detail"]
    assert any("invalid characters" in str(err).lower() for err in detail), (
        f"Expected XSS error, got: {detail}"
    )


def test_xss_in_bill_of_lading_rejected(client: TestClient, auth_headers):
    """Test that XSS in bill_of_lading is rejected."""
    payload = {
        "container_number": "CONT12345",
        "bill_of_lading": "javascript:alert('xss')",
        "weight_kg": 18000,
        "container_type": "40ft",
        "origin_port": "Callao",
        "destination_port": "Hamburg",
    }
    response = client.post("/shipments", json=payload, headers=auth_headers)
    assert response.status_code in [400, 422]
    detail = response.json()["detail"]
    assert any("invalid characters" in str(err).lower() for err in detail), (
        f"Expected XSS error, got: {detail}"
    )


def test_xss_in_notes_rejected(client: TestClient, auth_headers):
    """Test that XSS in notes is rejected."""
    payload = {
        "container_number": "CONT12345",
        "bill_of_lading": "BOL123456",
        "weight_kg": 18000,
        "container_type": "40ft",
        "origin_port": "Callao",
        "destination_port": "Hamburg",
        "notes": "Some notes <script>alert('xss')</script>",
    }
    response = client.post("/shipments", json=payload, headers=auth_headers)
    assert response.status_code in [400, 422]
    detail = response.json()["detail"]
    assert any("invalid characters" in str(err).lower() for err in detail), (
        f"Expected XSS error, got: {detail}"
    )


def test_xss_in_current_location_update_rejected(client: TestClient, auth_headers, db):
    """Test that XSS in current_location during update is rejected."""
    # First create a shipment
    shipment = Shipment(
        container_number="CONT_XSS_TEST",
        bill_of_lading="BOL_XSS_TEST",
        weight_kg=18000,
        container_type="40ft",
        origin_port="Callao",
        destination_port="Hamburg",
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    # Try to update with XSS
    update_payload = {
        "current_location": "Panama<script>alert('xss')</script>",
    }
    response = client.patch(
        f"/shipments/{shipment.id}", json=update_payload, headers=auth_headers
    )
    assert response.status_code in [400, 422]
    detail = response.json()["detail"]
    assert any("invalid characters" in str(err).lower() for err in detail), (
        f"Expected XSS error, got: {detail}"
    )


def test_xss_in_tracking_event_location_rejected(client: TestClient, auth_headers, db):
    """Test that XSS in tracking event location is rejected."""
    # First create a shipment
    shipment = Shipment(
        container_number="CONT_TRACK_TEST",
        bill_of_lading="BOL_TRACK_TEST",
        weight_kg=18000,
        container_type="40ft",
        origin_port="Callao",
        destination_port="Hamburg",
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    # Try to add tracking event with XSS in location
    event_payload = {
        "timestamp": "2024-01-20T10:30:00Z",
        "location": "Panama<script>alert('xss')</script>",
        "event": "Transit",
        "details": "Test event",
    }
    response = client.post(
        f"/shipments/{shipment.id}/track", json=event_payload, headers=auth_headers
    )
    assert response.status_code in [400, 422]
    detail = response.json()["detail"]
    assert any("invalid characters" in str(err).lower() for err in detail), (
        f"Expected XSS error, got: {detail}"
    )


def test_xss_in_tracking_event_event_field_rejected(
    client: TestClient, auth_headers, db
):
    """Test that XSS in tracking event event field is rejected."""
    # First create a shipment
    shipment = Shipment(
        container_number="CONT_EVENT_TEST",
        bill_of_lading="BOL_EVENT_TEST",
        weight_kg=18000,
        container_type="40ft",
        origin_port="Callao",
        destination_port="Hamburg",
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    # Try to add tracking event with XSS in event field
    event_payload = {
        "timestamp": "2024-01-20T10:30:00Z",
        "location": "Panama",
        "event": "Transit<iframe src='evil.com'></iframe>",
        "details": "Test event",
    }
    response = client.post(
        f"/shipments/{shipment.id}/track", json=event_payload, headers=auth_headers
    )
    assert response.status_code in [400, 422]
    detail = response.json()["detail"]
    assert any("invalid characters" in str(err).lower() for err in detail), (
        f"Expected XSS error, got: {detail}"
    )


def test_xss_in_tracking_event_details_rejected(client: TestClient, auth_headers, db):
    """Test that XSS in tracking event details is rejected."""
    # First create a shipment
    shipment = Shipment(
        container_number="CONT_DETAILS_TEST",
        bill_of_lading="BOL_DETAILS_TEST",
        weight_kg=18000,
        container_type="40ft",
        origin_port="Callao",
        destination_port="Hamburg",
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    # Try to add tracking event with XSS in details
    event_payload = {
        "timestamp": "2024-01-20T10:30:00Z",
        "location": "Panama",
        "event": "Transit",
        "details": "Some details javascript:alert('xss')",
    }
    response = client.post(
        f"/shipments/{shipment.id}/track", json=event_payload, headers=auth_headers
    )
    assert response.status_code in [400, 422]
    detail = response.json()["detail"]
    assert any("invalid characters" in str(err).lower() for err in detail), (
        f"Expected XSS error, got: {detail}"
    )


def test_valid_shipment_creation_succeeds(client: TestClient, auth_headers):
    """Test that valid shipment creation with clean data succeeds."""
    payload = {
        "container_number": "CONT_VALID_123",
        "bill_of_lading": "BOL_VALID_123",
        "weight_kg": 18000,
        "container_type": "40ft",
        "origin_port": "Callao, Peru",
        "destination_port": "Hamburg, Germany",
        "notes": "Regular shipment notes without any malicious content",
    }
    response = client.post("/shipments", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["origin_port"] == "Callao, Peru"
    assert data["destination_port"] == "Hamburg, Germany"
    assert data["notes"] == "Regular shipment notes without any malicious content"


def test_valid_tracking_event_succeeds(client: TestClient, auth_headers, db):
    """Test that valid tracking event with clean data succeeds."""
    # First create a shipment
    shipment = Shipment(
        container_number="CONT_VALID_TRACK",
        bill_of_lading="BOL_VALID_TRACK",
        weight_kg=18000,
        container_type="40ft",
        origin_port="Callao",
        destination_port="Hamburg",
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    # Add valid tracking event
    event_payload = {
        "timestamp": "2024-01-20T10:30:00Z",
        "location": "Panama Canal",
        "event": "Transit through canal",
        "details": "Successfully passed through Panama Canal",
    }
    response = client.post(
        f"/shipments/{shipment.id}/track", json=event_payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_location"] == "Panama Canal"
    assert len(data["tracking_events"]) == 1
    assert data["tracking_events"][0]["location"] == "Panama Canal"
