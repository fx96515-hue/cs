from app.models.shipment import Shipment
from app.models.cooperative import Cooperative
from app.models.lot import Lot


def test_create_shipment(client, auth_headers, db):
    """Test creating a new shipment."""
    payload = {
        "container_number": "MSCU1234567",
        "bill_of_lading": "BOL123456",
        "weight_kg": 18000.0,
        "container_type": "40ft",
        "origin_port": "Callao, Peru",
        "destination_port": "Hamburg, Germany",
        "departure_date": "2024-01-15",
        "estimated_arrival": "2024-02-20",
        "notes": "High quality specialty coffee",
    }

    response = client.post("/shipments", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["container_number"] == "MSCU1234567"
    assert data["weight_kg"] == 18000.0
    assert data["status"] == "in_transit"
    assert data["delay_hours"] == 0


def test_create_shipment_with_lot(client, auth_headers, db):
    """Test creating a shipment associated with a lot."""
    # Create cooperative first
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()
    db.refresh(coop)

    # Create lot
    lot = Lot(cooperative_id=coop.id, name="Test Lot", weight_kg=20000)
    db.add(lot)
    db.commit()
    db.refresh(lot)

    payload = {
        "lot_id": lot.id,
        "cooperative_id": coop.id,
        "container_number": "HLCU9876543",
        "bill_of_lading": "BOL789012",
        "weight_kg": 20000.0,
        "container_type": "40ft_hc",
        "origin_port": "Callao, Peru",
        "destination_port": "Rotterdam, Netherlands",
    }

    response = client.post("/shipments", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["lot_id"] == lot.id
    assert data["cooperative_id"] == coop.id


def test_create_duplicate_container_number(client, auth_headers, db):
    """Test that duplicate container numbers are rejected."""
    shipment = Shipment(
        container_number="DUPLICATE123",
        bill_of_lading="BOL001",
        weight_kg=15000,
        container_type="20ft",
        origin_port="Callao",
        destination_port="Hamburg",
    )
    db.add(shipment)
    db.commit()

    payload = {
        "container_number": "DUPLICATE123",
        "bill_of_lading": "BOL002",
        "weight_kg": 16000,
        "container_type": "20ft",
        "origin_port": "Callao",
        "destination_port": "Hamburg",
    }

    response = client.post("/shipments/", json=payload, headers=auth_headers)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data or "already exists" in str(data).lower()


def test_create_duplicate_bill_of_lading(client, auth_headers, db):
    """Test that duplicate bills of lading are rejected."""
    shipment = Shipment(
        container_number="CONT001",
        bill_of_lading="DUPLICATE_BOL",
        weight_kg=15000,
        container_type="20ft",
        origin_port="Callao",
        destination_port="Hamburg",
    )
    db.add(shipment)
    db.commit()

    payload = {
        "container_number": "CONT002",
        "bill_of_lading": "DUPLICATE_BOL",
        "weight_kg": 16000,
        "container_type": "20ft",
        "origin_port": "Callao",
        "destination_port": "Hamburg",
    }

    response = client.post("/shipments/", json=payload, headers=auth_headers)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data or "already exists" in str(data).lower()


def test_get_shipments_list(client, auth_headers, db):
    """Test retrieving list of shipments."""
    shipment1 = Shipment(
        container_number="TEST001",
        bill_of_lading="BOL001",
        weight_kg=15000,
        container_type="20ft",
        origin_port="Callao, Peru",
        destination_port="Hamburg, Germany",
        status="in_transit",
    )
    shipment2 = Shipment(
        container_number="TEST002",
        bill_of_lading="BOL002",
        weight_kg=18000,
        container_type="40ft",
        origin_port="Callao, Peru",
        destination_port="Rotterdam, Netherlands",
        status="delivered",
    )
    db.add_all([shipment1, shipment2])
    db.commit()

    response = client.get("/shipments", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_filter_shipments_by_status(client, auth_headers, db):
    """Test filtering shipments by status."""
    shipment1 = Shipment(
        container_number="STATUS001",
        bill_of_lading="BOL_STATUS001",
        weight_kg=15000,
        container_type="20ft",
        origin_port="Callao",
        destination_port="Hamburg",
        status="in_transit",
    )
    shipment2 = Shipment(
        container_number="STATUS002",
        bill_of_lading="BOL_STATUS002",
        weight_kg=16000,
        container_type="20ft",
        origin_port="Callao",
        destination_port="Hamburg",
        status="delivered",
    )
    db.add_all([shipment1, shipment2])
    db.commit()

    response = client.get("/shipments?status=in_transit", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(s["status"] == "in_transit" for s in data)


def test_filter_shipments_by_port(client, auth_headers, db):
    """Test filtering shipments by port."""
    shipment1 = Shipment(
        container_number="PORT001",
        bill_of_lading="BOL_PORT001",
        weight_kg=15000,
        container_type="20ft",
        origin_port="Callao, Peru",
        destination_port="Hamburg, Germany",
    )
    shipment2 = Shipment(
        container_number="PORT002",
        bill_of_lading="BOL_PORT002",
        weight_kg=16000,
        container_type="20ft",
        origin_port="Callao, Peru",
        destination_port="Rotterdam, Netherlands",
    )
    db.add_all([shipment1, shipment2])
    db.commit()

    response = client.get(
        "/shipments?destination_port=Hamburg, Germany", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert all(s["destination_port"] == "Hamburg, Germany" for s in data)


def test_get_active_shipments(client, auth_headers, db):
    """Test getting active shipments."""
    shipment1 = Shipment(
        container_number="ACTIVE001",
        bill_of_lading="BOL_ACTIVE001",
        weight_kg=15000,
        container_type="20ft",
        origin_port="Callao",
        destination_port="Hamburg",
        status="in_transit",
    )
    shipment2 = Shipment(
        container_number="ACTIVE002",
        bill_of_lading="BOL_ACTIVE002",
        weight_kg=16000,
        container_type="20ft",
        origin_port="Callao",
        destination_port="Hamburg",
        status="delivered",
    )
    db.add_all([shipment1, shipment2])
    db.commit()

    response = client.get("/shipments/active", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(s["status"] == "in_transit" for s in data)
    assert len(data) >= 1


def test_get_delayed_shipments(client, auth_headers, db):
    """Test getting delayed shipments."""
    shipment1 = Shipment(
        container_number="DELAY001",
        bill_of_lading="BOL_DELAY001",
        weight_kg=15000,
        container_type="20ft",
        origin_port="Callao",
        destination_port="Hamburg",
        delay_hours=48,
    )
    shipment2 = Shipment(
        container_number="DELAY002",
        bill_of_lading="BOL_DELAY002",
        weight_kg=16000,
        container_type="20ft",
        origin_port="Callao",
        destination_port="Hamburg",
        delay_hours=0,
    )
    db.add_all([shipment1, shipment2])
    db.commit()

    response = client.get("/shipments/delayed", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(s["delay_hours"] > 0 for s in data)


def test_get_shipment_by_id(client, auth_headers, db):
    """Test retrieving single shipment by ID."""
    shipment = Shipment(
        container_number="GETID001",
        bill_of_lading="BOL_GETID001",
        weight_kg=19000,
        container_type="40ft",
        origin_port="Callao, Peru",
        destination_port="Hamburg, Germany",
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    response = client.get(f"/shipments/{shipment.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == shipment.id
    assert data["container_number"] == "GETID001"


def test_update_shipment(client, auth_headers, db):
    """Test updating shipment data."""
    shipment = Shipment(
        container_number="UPDATE001",
        bill_of_lading="BOL_UPDATE001",
        weight_kg=18000,
        container_type="40ft",
        origin_port="Callao",
        destination_port="Hamburg",
        status="in_transit",
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    update_data = {
        "current_location": "Panama Canal",
        "status": "customs",
    }
    response = client.patch(
        f"/shipments/{shipment.id}", json=update_data, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_location"] == "Panama Canal"
    assert data["status"] == "customs"
    assert data["status_updated_at"] is not None


def test_update_shipment_delay(client, auth_headers, db):
    """Test updating shipment with delay information."""
    shipment = Shipment(
        container_number="DELAY_UPDATE001",
        bill_of_lading="BOL_DELAY_UPDATE001",
        weight_kg=18000,
        container_type="40ft",
        origin_port="Callao",
        destination_port="Hamburg",
        delay_hours=0,
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    update_data = {"delay_hours": 72}
    response = client.patch(
        f"/shipments/{shipment.id}", json=update_data, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["delay_hours"] == 72


def test_delete_shipment(client, auth_headers, db):
    """Test deleting a shipment."""
    shipment = Shipment(
        container_number="DELETE001",
        bill_of_lading="BOL_DELETE001",
        weight_kg=17000,
        container_type="40ft",
        origin_port="Callao",
        destination_port="Hamburg",
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    response = client.delete(f"/shipments/{shipment.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

    # Verify deletion
    response = client.get(f"/shipments/{shipment.id}", headers=auth_headers)
    assert response.status_code == 404


def test_add_tracking_event(client, auth_headers, db):
    """Test adding a tracking event to a shipment."""
    shipment = Shipment(
        container_number="TRACK001",
        bill_of_lading="BOL_TRACK001",
        weight_kg=18000,
        container_type="40ft",
        origin_port="Callao, Peru",
        destination_port="Hamburg, Germany",
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    event_payload = {
        "timestamp": "2024-01-20T10:30:00Z",
        "location": "Panama Canal",
        "event": "Transit",
        "details": "Passed through Panama Canal successfully",
    }

    response = client.post(
        f"/shipments/{shipment.id}/track", json=event_payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_location"] == "Panama Canal"
    assert len(data["tracking_events"]) == 1
    assert data["tracking_events"][0]["location"] == "Panama Canal"


def test_add_multiple_tracking_events(client, auth_headers, db):
    """Test adding multiple tracking events to a shipment."""
    shipment = Shipment(
        container_number="MULTITRACK001",
        bill_of_lading="BOL_MULTITRACK001",
        weight_kg=18000,
        container_type="40ft",
        origin_port="Callao, Peru",
        destination_port="Hamburg, Germany",
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    # Add first event
    event1 = {
        "timestamp": "2024-01-15T08:00:00Z",
        "location": "Callao Port",
        "event": "Departure",
    }
    client.post(f"/shipments/{shipment.id}/track", json=event1, headers=auth_headers)

    # Add second event
    event2 = {
        "timestamp": "2024-01-20T14:00:00Z",
        "location": "Panama Canal",
        "event": "Transit",
    }
    response = client.post(
        f"/shipments/{shipment.id}/track", json=event2, headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["tracking_events"]) == 2
    assert data["current_location"] == "Panama Canal"


def test_shipment_validation_container_type(client, auth_headers):
    """Test container type validation."""
    payload = {
        "container_number": "INVALID001",
        "bill_of_lading": "BOL_INVALID001",
        "weight_kg": 18000,
        "container_type": "invalid_type",  # Invalid container type
        "origin_port": "Callao",
        "destination_port": "Hamburg",
    }

    response = client.post("/shipments", json=payload, headers=auth_headers)
    assert response.status_code == 422  # Validation error


def test_shipment_validation_weight(client, auth_headers):
    """Test weight validation."""
    payload = {
        "container_number": "WEIGHT001",
        "bill_of_lading": "BOL_WEIGHT001",
        "weight_kg": -1000,  # Invalid negative weight
        "container_type": "40ft",
        "origin_port": "Callao",
        "destination_port": "Hamburg",
    }

    response = client.post("/shipments", json=payload, headers=auth_headers)
    assert response.status_code == 422  # Validation error


def test_shipment_unauthorized_access(client):
    """Test that accessing shipments without token fails."""
    response = client.get("/shipments")
    assert response.status_code == 401


def test_shipment_viewer_cannot_create(client, viewer_auth_headers):
    """Test that viewer role cannot create shipments."""
    payload = {
        "container_number": "VIEWER001",
        "bill_of_lading": "BOL_VIEWER001",
        "weight_kg": 18000,
        "container_type": "40ft",
        "origin_port": "Callao",
        "destination_port": "Hamburg",
    }

    response = client.post("/shipments", json=payload, headers=viewer_auth_headers)
    assert response.status_code == 403


def test_shipment_viewer_can_read(client, viewer_auth_headers, db):
    """Test that viewer role can read shipments."""
    shipment = Shipment(
        container_number="VIEWABLE001",
        bill_of_lading="BOL_VIEWABLE001",
        weight_kg=18000,
        container_type="40ft",
        origin_port="Callao",
        destination_port="Hamburg",
    )
    db.add(shipment)
    db.commit()

    response = client.get("/shipments", headers=viewer_auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_nonexistent_shipment(client, auth_headers):
    """Test getting a shipment that doesn't exist."""
    response = client.get("/shipments/99999", headers=auth_headers)
    assert response.status_code == 404


def test_update_nonexistent_shipment(client, auth_headers):
    """Test updating a shipment that doesn't exist."""
    response = client.patch(
        "/shipments/99999", json={"status": "delivered"}, headers=auth_headers
    )
    assert response.status_code == 404


def test_delete_nonexistent_shipment(client, auth_headers):
    """Test deleting a shipment that doesn't exist."""
    response = client.delete("/shipments/99999", headers=auth_headers)
    assert response.status_code == 404


def test_add_tracking_event_nonexistent_shipment(client, auth_headers):
    """Test adding tracking event to non-existent shipment."""
    event_payload = {
        "timestamp": "2024-01-20T10:30:00Z",
        "location": "Test Location",
        "event": "Test Event",
    }
    response = client.post(
        "/shipments/99999/track", json=event_payload, headers=auth_headers
    )
    assert response.status_code == 404
