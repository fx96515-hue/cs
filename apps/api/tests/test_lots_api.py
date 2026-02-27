"""Tests for lots API routes."""

from app.models.lot import Lot
from app.models.cooperative import Cooperative


def test_list_lots_empty(client, auth_headers, db):
    """Test listing lots when none exist."""
    response = client.get("/lots", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_create_lot(client, auth_headers, db):
    """Test creating a new lot."""
    # Create a cooperative first
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()
    db.refresh(coop)

    payload = {
        "cooperative_id": coop.id,
        "name": "LOT-001",
        "crop_year": 2024,
        "varieties": "Caturra",
        "processing": "washed",
        "weight_kg": 1000.0,
    }

    response = client.post("/lots", json=payload, headers=auth_headers)

    assert response.status_code == 200 or response.status_code == 201
    data = response.json()
    assert data["name"] == "LOT-001"
    assert data["cooperative_id"] == coop.id


def test_list_lots_with_data(client, auth_headers, db):
    """Test listing lots with existing data."""
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()

    lot1 = Lot(cooperative_id=coop.id, name="LOT-001", crop_year=2024)
    lot2 = Lot(cooperative_id=coop.id, name="LOT-002", crop_year=2024)
    db.add_all([lot1, lot2])
    db.commit()

    response = client.get("/lots", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_get_lot_by_id(client, auth_headers, db):
    """Test getting a specific lot by ID."""
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()

    lot = Lot(cooperative_id=coop.id, name="LOT-001", crop_year=2024)
    db.add(lot)
    db.commit()
    db.refresh(lot)

    response = client.get(f"/lots/{lot.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == lot.id
    assert data["name"] == "LOT-001"


def test_get_lot_not_found(client, auth_headers, db):
    """Test getting a non-existent lot."""
    response = client.get("/lots/99999", headers=auth_headers)

    assert response.status_code == 404


def test_update_lot(client, auth_headers, db):
    """Test updating a lot."""
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()

    lot = Lot(cooperative_id=coop.id, name="LOT-001", crop_year=2024)
    db.add(lot)
    db.commit()
    db.refresh(lot)

    update_payload = {"varieties": "Bourbon"}
    response = client.patch(
        f"/lots/{lot.id}", json=update_payload, headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["varieties"] == "Bourbon"


def test_delete_lot(client, auth_headers, db):
    """Test deleting a lot."""
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()

    lot = Lot(cooperative_id=coop.id, name="LOT-001", crop_year=2024)
    db.add(lot)
    db.commit()
    db.refresh(lot)

    response = client.delete(f"/lots/{lot.id}", headers=auth_headers)

    assert response.status_code == 200 or response.status_code == 204


def test_list_lots_filter_by_cooperative(client, auth_headers, db):
    """Test listing lots filtered by cooperative ID."""
    coop1 = Cooperative(name="Coop 1", region="Cajamarca")
    coop2 = Cooperative(name="Coop 2", region="Junin")
    db.add_all([coop1, coop2])
    db.commit()

    lot1 = Lot(cooperative_id=coop1.id, name="LOT-001", crop_year=2024)
    lot2 = Lot(cooperative_id=coop2.id, name="LOT-002", crop_year=2024)
    db.add_all([lot1, lot2])
    db.commit()

    response = client.get(f"/lots?cooperative_id={coop1.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert all(lot["cooperative_id"] == coop1.id for lot in data)


def test_create_lot_unauthorized(client, viewer_auth_headers, db):
    """Test that viewers cannot create lots."""
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()

    payload = {"cooperative_id": coop.id, "name": "LOT-001", "crop_year": 2024}

    response = client.post("/lots", json=payload, headers=viewer_auth_headers)

    assert response.status_code == 403


def test_viewer_can_read_lots(client, viewer_auth_headers, db):
    """Test that viewers can read lots."""
    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()

    lot = Lot(cooperative_id=coop.id, name="LOT-001", crop_year=2024)
    db.add(lot)
    db.commit()

    response = client.get("/lots", headers=viewer_auth_headers)

    assert response.status_code == 200


def test_lots_without_auth(client, db):
    """Test accessing lots without authentication."""
    response = client.get("/lots")

    assert response.status_code == 401
