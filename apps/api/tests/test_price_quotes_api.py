"""Tests for price quote API routes."""

from datetime import datetime, timezone


def _quote_payload(**overrides):
    payload = {
        "lot_id": 1,
        "price_per_kg": 7.25,
        "currency": "USD",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "confidence": 0.82,
        "notes": "spot quote",
        "meta": {"source": "unit-test"},
    }
    payload.update(overrides)
    return payload


def test_price_quotes_crud_flow(client, auth_headers):
    create_response = client.post(
        "/price-quotes/",
        json=_quote_payload(),
        headers=auth_headers,
    )
    assert create_response.status_code == 200
    created = create_response.json()
    quote_id = created["id"]
    assert created["currency"] == "USD"

    get_response = client.get(f"/price-quotes/{quote_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == quote_id

    patch_response = client.patch(
        f"/price-quotes/{quote_id}",
        json={"price_per_kg": 7.9, "currency": "eur"},
        headers=auth_headers,
    )
    assert patch_response.status_code == 200
    updated = patch_response.json()
    assert updated["price_per_kg"] == 7.9
    assert updated["currency"] == "EUR"

    list_response = client.get("/price-quotes/?lot_id=1&limit=10", headers=auth_headers)
    assert list_response.status_code == 200
    listed_ids = [item["id"] for item in list_response.json()]
    assert quote_id in listed_ids

    delete_response = client.delete(f"/price-quotes/{quote_id}", headers=auth_headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "deleted"

    missing_after_delete = client.get(f"/price-quotes/{quote_id}", headers=auth_headers)
    assert missing_after_delete.status_code == 404


def test_price_quotes_not_found_paths(client, auth_headers):
    patch_response = client.patch(
        "/price-quotes/99999",
        json={"price_per_kg": 5.0},
        headers=auth_headers,
    )
    assert patch_response.status_code == 404

    delete_response = client.delete("/price-quotes/99999", headers=auth_headers)
    assert delete_response.status_code == 404


def test_price_quotes_viewer_read_only(client, auth_headers, viewer_auth_headers):
    create_response = client.post(
        "/price-quotes/",
        json=_quote_payload(),
        headers=auth_headers,
    )
    assert create_response.status_code == 200
    quote_id = create_response.json()["id"]

    list_response = client.get("/price-quotes/?limit=5", headers=viewer_auth_headers)
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    get_response = client.get(f"/price-quotes/{quote_id}", headers=viewer_auth_headers)
    assert get_response.status_code == 200

    forbidden_create = client.post(
        "/price-quotes/",
        json=_quote_payload(price_per_kg=9.1),
        headers=viewer_auth_headers,
    )
    assert forbidden_create.status_code == 403

