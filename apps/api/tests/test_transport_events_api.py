"""Tests for transport event API routes."""

from datetime import datetime, timezone


def _event_payload(**overrides):
    payload = {
        "shipment_id": 1,
        "event_type": "departed",
        "location": "Callao",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "status": "in_transit",
        "details": {"note": "left port"},
    }
    payload.update(overrides)
    return payload


def test_transport_events_crud_flow(client, auth_headers):
    create_response = client.post(
        "/transport-events/",
        json=_event_payload(),
        headers=auth_headers,
    )
    assert create_response.status_code == 200
    created = create_response.json()
    event_id = created["id"]
    assert created["event_type"] == "departed"

    get_response = client.get(f"/transport-events/{event_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == event_id

    list_response = client.get(
        "/transport-events/?shipment_id=1&limit=25",
        headers=auth_headers,
    )
    assert list_response.status_code == 200
    listed_ids = [item["id"] for item in list_response.json()]
    assert event_id in listed_ids

    delete_response = client.delete(
        f"/transport-events/{event_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "deleted"

    missing_after_delete = client.get(
        f"/transport-events/{event_id}",
        headers=auth_headers,
    )
    assert missing_after_delete.status_code == 404


def test_transport_events_not_found_paths(client, auth_headers):
    get_response = client.get("/transport-events/99999", headers=auth_headers)
    assert get_response.status_code == 404

    delete_response = client.delete("/transport-events/99999", headers=auth_headers)
    assert delete_response.status_code == 404


def test_transport_events_viewer_read_only(client, auth_headers, viewer_auth_headers):
    create_response = client.post(
        "/transport-events/",
        json=_event_payload(event_type="arrived"),
        headers=auth_headers,
    )
    assert create_response.status_code == 200
    event_id = create_response.json()["id"]

    list_response = client.get(
        "/transport-events/?shipment_id=1",
        headers=viewer_auth_headers,
    )
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    get_response = client.get(
        f"/transport-events/{event_id}",
        headers=viewer_auth_headers,
    )
    assert get_response.status_code == 200

    forbidden_create = client.post(
        "/transport-events/",
        json=_event_payload(event_type="customs"),
        headers=viewer_auth_headers,
    )
    assert forbidden_create.status_code == 403

