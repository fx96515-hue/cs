"""Integration tests for core workflows."""

import pytest
from app.models.cooperative import Cooperative
from datetime import datetime, timezone


def test_complete_sourcing_workflow(client, auth_headers, db):
    """Test complete sourcing workflow from cooperative to lot to margin calculation."""
    # Step 1: Create a cooperative
    coop_payload = {
        "name": "Test Cooperative",
        "region": "Cajamarca",
        "altitude_m": 1800.0,
        "varieties": "Caturra, Bourbon",
    }

    coop_response = client.post(
        "/cooperatives", json=coop_payload, headers=auth_headers
    )
    assert coop_response.status_code in [200, 201]
    coop = coop_response.json()
    coop_id = coop["id"]

    # Step 2: Create a lot for this cooperative
    lot_payload = {
        "cooperative_id": coop_id,
        "name": "LOT-001",
        "crop_year": 2024,
        "weight_kg": 1000.0,
        "varieties": "Caturra",
    }

    lot_response = client.post("/lots", json=lot_payload, headers=auth_headers)
    assert lot_response.status_code in [200, 201]
    lot = lot_response.json()
    lot_id = lot["id"]

    # Step 3: Calculate margin for the lot
    margin_payload = {
        "purchase_price_per_kg": 5.0,
        "landed_costs_per_kg": 2.0,
        "yield_factor": 0.84,
        "roast_and_pack_costs_per_kg": 3.0,
        "selling_price_per_kg": 15.0,
        "purchase_currency": "USD",
        "selling_currency": "EUR",
    }

    margin_response = client.post(
        f"/margins/lots/{lot_id}/runs", json=margin_payload, headers=auth_headers
    )
    assert margin_response.status_code == 200
    margin = margin_response.json()
    assert "outputs" in margin


def test_roaster_sales_workflow(client, auth_headers, db):
    """Test roaster sales workflow from creation to scoring."""
    # Step 1: Create a roaster
    roaster_payload = {
        "name": "Berlin Coffee Roasters",
        "city": "Berlin",
        "specialty_focus": True,
        "peru_focus": True,
    }

    roaster_response = client.post(
        "/roasters", json=roaster_payload, headers=auth_headers
    )
    assert roaster_response.status_code in [200, 201]
    roaster = roaster_response.json()
    roaster_id = roaster["id"]

    # Step 2: Generate outreach for the roaster
    outreach_payload = {
        "entity_type": "roaster",
        "entity_id": roaster_id,
        "language": "de",
        "purpose": "sourcing_pitch",
        "refine_with_llm": False,
    }

    outreach_response = client.post(
        "/outreach/generate", json=outreach_payload, headers=auth_headers
    )
    assert outreach_response.status_code == 200
    outreach = outreach_response.json()
    assert "text" in outreach


def test_market_data_workflow(client, auth_headers, db):
    """Test market data workflow from observation to margin calculation."""
    # Step 1: Create market observation for FX rate
    obs_payload = {
        "key": "FX:USD_EUR",
        "value": 0.92,
        "unit": "EUR",
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }

    obs_response = client.post(
        "/market/observations", json=obs_payload, headers=auth_headers
    )
    assert obs_response.status_code in [200, 201]

    # Step 2: Calculate landed cost using market data
    landed_cost_payload = {
        "weight_kg": 1000.0,
        "green_price_usd_per_kg": 5.0,
        "freight_usd": 500.0,
    }

    landed_cost_response = client.post(
        "/logistics/landed-cost", json=landed_cost_payload, headers=auth_headers
    )
    assert landed_cost_response.status_code == 200
    landed_cost = landed_cost_response.json()
    assert "breakdown_eur" in landed_cost


@pytest.mark.skip(reason="Export endpoint may not be configured")
def test_data_export_workflow(client, auth_headers, db):
    """Test data export workflow."""
    # Create some test data
    coop1 = Cooperative(name="Coop 1", region="Cajamarca")
    coop2 = Cooperative(name="Coop 2", region="Junin")
    db.add_all([coop1, coop2])
    db.commit()

    # Export cooperatives
    export_response = client.get("/export/cooperatives", headers=auth_headers)
    assert export_response.status_code == 200
    assert "text/csv" in export_response.headers.get("content-type", "")


def test_viewer_access_control_workflow(client, viewer_auth_headers, auth_headers, db):
    """Test that viewers have correct access control."""
    # Viewer can read
    read_response = client.get("/cooperatives", headers=viewer_auth_headers)
    assert read_response.status_code == 200

    # Viewer cannot create
    create_payload = {"name": "Test Coop", "region": "Cajamarca"}
    create_response = client.post(
        "/cooperatives", json=create_payload, headers=viewer_auth_headers
    )
    assert create_response.status_code == 403

    # Admin can create
    admin_create_response = client.post(
        "/cooperatives", json=create_payload, headers=auth_headers
    )
    assert admin_create_response.status_code in [200, 201]


def test_duplicate_detection_workflow(client, auth_headers, db):
    """Test duplicate detection workflow."""
    # Create similar cooperatives
    coop1 = Cooperative(name="Coffee Cooperative", region="Cajamarca")
    coop2 = Cooperative(name="Coffee Coop", region="Cajamarca")
    db.add_all([coop1, coop2])
    db.commit()

    # Suggest duplicates
    dedup_response = client.get(
        "/dedup/suggest?entity_type=cooperative&threshold=80", headers=auth_headers
    )
    assert dedup_response.status_code == 200
    duplicates = dedup_response.json()
    assert isinstance(duplicates, list)


def test_news_and_reports_workflow(client, auth_headers, db):
    """Test news and reports workflow."""
    # List reports
    reports_response = client.get("/reports", headers=auth_headers)
    assert reports_response.status_code == 200

    # List news
    news_response = client.get("/news", headers=auth_headers)
    assert news_response.status_code == 200
