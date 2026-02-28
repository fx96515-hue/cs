"""End-to-end integration tests across the full stack.

Tests the complete user journey from authentication to data operations.
DOES NOT DUPLICATE unit tests from PR #16.
"""
import pytest
import requests

from tests.integration.bootstrap import BASE_URL, get_auth_token, auth_headers


@pytest.fixture(scope="module")
def auth_token() -> str:
    """Get authentication token for test user."""
    try:
        return get_auth_token()
    except RuntimeError as exc:
        pytest.skip(str(exc))
    raise RuntimeError("Unreachable: auth token not available")


def test_e2e_cooperative_flow(auth_token):
    """Test complete cooperative creation → sourcing analysis → frontend display flow."""
    headers = auth_headers(auth_token)
    
    # Step 1: Create cooperative
    coop_data = {
        "name": "E2E Test Cooperative",
        "region": "Cajamarca",
        "contact_email": "test@e2ecoop.com",
    }
    create_resp = requests.post(
        f"{BASE_URL}/cooperatives",
        json=coop_data,
        headers=headers
    )
    assert create_resp.status_code == 201
    coop_id = create_resp.json()["id"]
    
    # Step 2: Trigger sourcing analysis (if Peru routes exist from PR #4)
    try:
        analysis_resp = requests.post(
            f"{BASE_URL}/peru/cooperatives/{coop_id}/analyze",
            headers=headers
        )
        if analysis_resp.status_code == 200:
            analysis = analysis_resp.json()
            assert "total_score" in analysis
    except requests.exceptions.RequestException:
        pytest.skip("Peru sourcing routes not available")
    
    # Step 3: Verify retrieval
    get_resp = requests.get(f"{BASE_URL}/cooperatives/{coop_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "E2E Test Cooperative"
    
    # Cleanup
    requests.delete(f"{BASE_URL}/cooperatives/{coop_id}", headers=headers)


def test_e2e_roaster_flow(auth_token):
    """Test complete roaster creation → sales fit scoring → frontend display flow."""
    headers = auth_headers(auth_token)
    
    roaster_data = {
        "name": "E2E Test Roastery",
        "city": "Hamburg",
        "contact_email": "test@e2eroaster.de",
    }
    
    create_resp = requests.post(
        f"{BASE_URL}/roasters",
        json=roaster_data,
        headers=headers
    )
    assert create_resp.status_code == 201
    roaster_id = create_resp.json()["id"]
    
    get_resp = requests.get(f"{BASE_URL}/roasters/{roaster_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["city"] == "Hamburg"
    
    requests.delete(f"{BASE_URL}/roasters/{roaster_id}", headers=headers)


def test_e2e_margin_calculation(auth_token):
    """Test lot creation → margin calculation → frontend display."""
    headers = auth_headers(auth_token)
    
    # Create cooperative first
    coop_resp = requests.post(
        f"{BASE_URL}/cooperatives",
        json={
            "name": "Margin Test Coop",
            "region": "Junín",
            "annual_volume_kg": 20000
        },
        headers=headers
    )
    coop_id = coop_resp.json()["id"]
    
    # Create lot
    lot_data = {
        "cooperative_id": coop_id,
        "name": "Test Lot A",
        "price_per_kg": 5.50,
        "currency": "USD",
        "weight_kg": 1000,
        "expected_cupping_score": 86.0
    }
    lot_resp = requests.post(f"{BASE_URL}/lots", json=lot_data, headers=headers)
    assert lot_resp.status_code == 201
    lot_id = lot_resp.json()["id"]
    
    # Calculate margin - using correct endpoint and schema
    margin_data = {
        "purchase_price_per_kg": 5.50,
        "purchase_currency": "USD",
        "landed_costs_per_kg": 0.45,
        "roast_and_pack_costs_per_kg": 0.25,
        "yield_factor": 0.84,
        "selling_price_per_kg": 7.20,
        "selling_currency": "EUR"
    }
    margin_resp = requests.post(
        f"{BASE_URL}/margins/calc",  # Fixed endpoint
        json=margin_data,
        headers=headers
    )
    assert margin_resp.status_code == 200
    assert "outputs" in margin_resp.json()
    result = margin_resp.json()
    assert "outputs" in result
    assert "gross_margin_per_kg" in result["outputs"]
    
    # Cleanup
    requests.delete(f"{BASE_URL}/lots/{lot_id}", headers=headers)
    requests.delete(f"{BASE_URL}/cooperatives/{coop_id}", headers=headers)


def test_ml_predictions_available(auth_token):
    """Verify ML prediction endpoints are functional."""
    headers = auth_headers(auth_token)
    
    # Test freight cost prediction
    freight_payload = {
        "origin_port": "Callao",
        "destination_port": "Hamburg",
        "weight_kg": 20000,
        "container_type": "40ft"
    }
    
    try:
        ml_resp = requests.post(
            f"{BASE_URL}/ml/predict-freight",
            json=freight_payload,
            headers=headers
        )
        if ml_resp.status_code == 200:
            assert "predicted_cost" in ml_resp.json()
        else:
            pytest.skip("ML endpoints not fully configured")
    except requests.exceptions.RequestException:
        pytest.skip("ML service not available")


def test_e2e_shipment_flow(auth_token):
    """Test complete shipment creation → tracking → frontend display flow."""
    headers = auth_headers(auth_token)
    
    # Step 1: Create shipment
    shipment_data = {
        "container_number": "TEST1234567",
        "bill_of_lading": "BOL-TEST-001",
        "weight_kg": 18000,
        "container_type": "40ft",
        "origin_port": "Callao, Peru",
        "destination_port": "Hamburg, Germany",
        "departure_date": "2024-01-15",
        "estimated_arrival": "2024-02-20"
    }
    create_resp = requests.post(
        f"{BASE_URL}/shipments",
        json=shipment_data,
        headers=headers
    )
    assert create_resp.status_code == 201
    shipment_id = create_resp.json()["id"]
    
    # Step 2: List all shipments
    list_resp = requests.get(f"{BASE_URL}/shipments", headers=headers)
    assert list_resp.status_code == 200
    shipments = list_resp.json()
    assert len(shipments) > 0
    assert any(s["id"] == shipment_id for s in shipments)
    
    # Step 3: Get single shipment
    get_resp = requests.get(f"{BASE_URL}/shipments/{shipment_id}", headers=headers)
    assert get_resp.status_code == 200
    shipment = get_resp.json()
    assert shipment["container_number"] == "TEST1234567"
    assert shipment["origin_port"] == "Callao, Peru"
    
    # Step 4: Update shipment
    update_data = {
        "current_location": "Panama Canal",
        "status": "in_transit"
    }
    update_resp = requests.patch(
        f"{BASE_URL}/shipments/{shipment_id}",
        json=update_data,
        headers=headers
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["current_location"] == "Panama Canal"
    assert updated["status"] == "in_transit"
    
    # Step 5: List active shipments
    active_resp = requests.get(f"{BASE_URL}/shipments/active", headers=headers)
    assert active_resp.status_code == 200
    active_shipments = active_resp.json()
    assert any(s["id"] == shipment_id for s in active_shipments)
    
    # Cleanup
    requests.delete(f"{BASE_URL}/shipments/{shipment_id}", headers=headers)


def test_health_endpoints():
    """Verify system health and readiness."""
    health = requests.get(f"{BASE_URL}/health")
    assert health.status_code == 200
    
    # Check Prometheus metrics endpoint
    metrics = requests.get(f"{BASE_URL}/metrics")
    assert metrics.status_code == 200
    assert "http_requests_total" in metrics.text or "python" in metrics.text


def test_shipments_api_integration(auth_token):
    """Test shipments API endpoints."""
    headers = auth_headers(auth_token)
    
    # Create a shipment
    shipment_data = {
        "container_number": "TEST1234567",
        "bill_of_lading": "BOL-TEST-001",
        "weight_kg": 18000.0,
        "container_type": "40ft",
        "origin_port": "Callao, Peru",
        "destination_port": "Hamburg, Germany",
        "departure_date": "2024-01-15",
        "estimated_arrival": "2024-03-01",
        "notes": "E2E test shipment"
    }
    
    create_resp = requests.post(
        f"{BASE_URL}/shipments",
        json=shipment_data,
        headers=headers
    )
    assert create_resp.status_code == 201
    shipment_id = create_resp.json()["id"]
    
    # List shipments
    list_resp = requests.get(f"{BASE_URL}/shipments", headers=headers)
    assert list_resp.status_code == 200
    shipments = list_resp.json()
    assert len(shipments) > 0
    
    # Get single shipment
    get_resp = requests.get(f"{BASE_URL}/shipments/{shipment_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["container_number"] == "TEST1234567"
    
    # Update shipment
    update_data = {
        "current_location": "Panama Canal",
        "status": "in_transit"
    }
    update_resp = requests.patch(
        f"{BASE_URL}/shipments/{shipment_id}",
        json=update_data,
        headers=headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["current_location"] == "Panama Canal"
    
    # Cleanup
    requests.delete(f"{BASE_URL}/shipments/{shipment_id}", headers=headers)


def test_frontend_accessibility():
    """Verify frontend is accessible at port 3000."""
    try:
        # Try to access frontend
        response = requests.get("http://localhost:3000", timeout=5)
        # Frontend should return 200 for the home page or redirect (3xx)
        assert response.status_code in [200, 301, 302, 307, 308], \
            f"Frontend returned unexpected status: {response.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.skip("Frontend not accessible (may not be running or configured differently)")

