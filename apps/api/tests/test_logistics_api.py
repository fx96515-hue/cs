"""Tests for logistics API routes."""


def test_landed_cost_calculation(client, auth_headers, db):
    """Test landed cost calculation endpoint."""
    payload = {
        "weight_kg": 1000.0,
        "green_price_usd_per_kg": 5.0,
        "incoterm": "FOB",
        "freight_usd": 500.0,
        "insurance_pct": 0.006,
        "handling_eur": 100.0,
        "inland_trucking_eur": 150.0,
        "duty_pct": 0.0,
        "vat_pct": 0.19,
    }

    response = client.post("/logistics/landed-cost", json=payload, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "breakdown_eur" in data


def test_landed_cost_with_duty(client, auth_headers, db):
    """Test landed cost calculation with customs duty."""
    payload = {"weight_kg": 1000.0, "green_price_usd_per_kg": 5.0, "duty_pct": 0.10}

    response = client.post("/logistics/landed-cost", json=payload, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["breakdown_eur"]["duty"] > 0


def test_landed_cost_unauthorized(client, db):
    """Test landed cost without authentication."""
    payload = {"weight_kg": 1000.0, "green_price_usd_per_kg": 5.0}

    response = client.post("/logistics/landed-cost", json=payload)

    assert response.status_code == 401


def test_landed_cost_viewer_can_access(client, viewer_auth_headers, db):
    """Test that viewers can calculate landed cost."""
    payload = {"weight_kg": 1000.0, "green_price_usd_per_kg": 5.0}

    response = client.post(
        "/logistics/landed-cost", json=payload, headers=viewer_auth_headers
    )

    assert response.status_code == 200


def test_landed_cost_different_incoterms(client, auth_headers, db):
    """Test landed cost with different incoterms."""
    incoterms = ["FOB", "CIF", "EXW"]

    for incoterm in incoterms:
        payload = {
            "weight_kg": 1000.0,
            "green_price_usd_per_kg": 5.0,
            "incoterm": incoterm,
        }

        response = client.post(
            "/logistics/landed-cost", json=payload, headers=auth_headers
        )

        assert response.status_code == 200
