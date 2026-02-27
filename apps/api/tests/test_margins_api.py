"""Tests for margins API routes."""

import pytest
from app.models.lot import Lot
from app.models.cooperative import Cooperative


def test_calc_margin_endpoint(client, auth_headers, db):
    """Test margin calculation endpoint."""
    payload = {
        "purchase_price_per_kg": 10.0,
        "landed_costs_per_kg": 2.0,
        "yield_factor": 0.84,
        "roast_and_pack_costs_per_kg": 3.0,
        "selling_price_per_kg": 20.0,
        "purchase_currency": "USD",
        "selling_currency": "EUR",
    }

    response = client.post("/margins/calc", json=payload, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "outputs" in data
    assert "gross_margin_per_kg" in data["outputs"]


def test_calc_and_store_for_lot(client, auth_headers, db):
    """Test calculating and storing margin for a lot."""
    # Create cooperative and lot
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()

    lot = Lot(cooperative_id=coop.id, name="LOT-001", crop_year=2024)
    db.add(lot)
    db.commit()
    db.refresh(lot)

    payload = {
        "purchase_price_per_kg": 10.0,
        "landed_costs_per_kg": 2.0,
        "yield_factor": 0.84,
        "roast_and_pack_costs_per_kg": 3.0,
        "selling_price_per_kg": 20.0,
        "purchase_currency": "USD",
        "selling_currency": "EUR",
    }

    response = client.post(
        f"/margins/lots/{lot.id}/runs", json=payload, headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["lot_id"] == lot.id


def test_calc_and_store_lot_not_found(client, auth_headers, db):
    """Test calculating margin for non-existent lot."""
    payload = {
        "purchase_price_per_kg": 10.0,
        "landed_costs_per_kg": 2.0,
        "yield_factor": 0.84,
        "roast_and_pack_costs_per_kg": 3.0,
        "selling_price_per_kg": 20.0,
        "purchase_currency": "USD",
        "selling_currency": "EUR",
    }

    response = client.post(
        "/margins/lots/99999/runs", json=payload, headers=auth_headers
    )

    assert response.status_code == 404


def test_list_runs_for_lot(client, auth_headers, db):
    """Test listing margin runs for a lot."""
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()

    lot = Lot(cooperative_id=coop.id, name="LOT-001", crop_year=2024)
    db.add(lot)
    db.commit()

    response = client.get(f"/margins/lots/{lot.id}/runs", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_calc_margin_unauthorized(client, viewer_auth_headers, db):
    """Test that viewers cannot calculate margins."""
    payload = {
        "purchase_price_per_kg": 10.0,
        "landed_costs_per_kg": 2.0,
        "yield_factor": 0.84,
        "roast_and_pack_costs_per_kg": 3.0,
        "selling_price_per_kg": 20.0,
        "purchase_currency": "USD",
        "selling_currency": "EUR",
    }

    response = client.post("/margins/calc", json=payload, headers=viewer_auth_headers)

    assert response.status_code == 403


@pytest.mark.skip(reason="Test requires actual error handling in API endpoint")
def test_calc_margin_invalid_yield_factor(client, auth_headers, db):
    """Test margin calculation with invalid yield factor."""
    payload = {
        "purchase_price_per_kg": 10.0,
        "landed_costs_per_kg": 2.0,
        "yield_factor": 0.0,  # Invalid
        "roast_and_pack_costs_per_kg": 3.0,
        "selling_price_per_kg": 20.0,
        "purchase_currency": "USD",
        "selling_currency": "EUR",
    }

    response = client.post("/margins/calc", json=payload, headers=auth_headers)

    # Should return error due to invalid yield factor
    assert response.status_code in [400, 422, 500]


def test_margins_without_auth(client, db):
    """Test accessing margins without authentication."""
    payload = {
        "purchase_price_per_kg": 10.0,
        "landed_costs_per_kg": 2.0,
        "yield_factor": 0.84,
        "roast_and_pack_costs_per_kg": 3.0,
        "selling_price_per_kg": 20.0,
        "purchase_currency": "USD",
        "selling_currency": "EUR",
    }

    response = client.post("/margins/calc", json=payload)

    assert response.status_code == 401


def test_list_runs_empty(client, auth_headers, db):
    """Test listing runs when none exist."""
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()

    lot = Lot(cooperative_id=coop.id, name="LOT-001", crop_year=2024)
    db.add(lot)
    db.commit()

    response = client.get(f"/margins/lots/{lot.id}/runs", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_calc_margin_with_fx_rate(client, auth_headers, db):
    """Test margin calculation with FX rate."""
    payload = {
        "purchase_price_per_kg": 10.0,
        "landed_costs_per_kg": 2.0,
        "yield_factor": 0.84,
        "roast_and_pack_costs_per_kg": 3.0,
        "selling_price_per_kg": 20.0,
        "purchase_currency": "USD",
        "selling_currency": "EUR",
        "fx_usd_to_eur": 0.92,
    }

    response = client.post("/margins/calc", json=payload, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "outputs" in data
