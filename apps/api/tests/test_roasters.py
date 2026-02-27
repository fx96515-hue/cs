from app.models.roaster import Roaster


def test_create_roaster(client, auth_headers, db):
    """Test creating a new roaster."""
    payload = {
        "name": "Berlin Coffee Roasters",
        "city": "Berlin",
        "website": "https://berlin-roasters.de",
        "contact_email": "info@berlin-roasters.de",
        "peru_focus": True,
        "specialty_focus": True,
        "price_position": "premium",
        "notes": "Focus on single-origin specialty",
        "status": "active",
    }

    response = client.post("/roasters", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Berlin Coffee Roasters"
    assert data["city"] == "Berlin"
    assert data["peru_focus"] is True
    assert data["specialty_focus"] is True
    assert data["price_position"] == "premium"


def test_get_roasters_list(client, auth_headers, db):
    """Test retrieving list of roasters."""
    # Create test roasters
    roaster1 = Roaster(name="Hamburg Roastery", city="Hamburg", peru_focus=False)
    roaster2 = Roaster(name="Munich Coffee", city="Munich", peru_focus=True)
    db.add_all([roaster1, roaster2])
    db.commit()

    response = client.get("/roasters", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert any(r["name"] == "Hamburg Roastery" for r in data)
    assert any(r["name"] == "Munich Coffee" for r in data)


def test_get_roaster_by_id(client, auth_headers, db):
    """Test retrieving single roaster by ID."""
    roaster = Roaster(name="Test Roaster", city="Frankfurt", specialty_focus=True)
    db.add(roaster)
    db.commit()
    db.refresh(roaster)

    response = client.get(f"/roasters/{roaster.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == roaster.id
    assert data["name"] == "Test Roaster"
    assert data["city"] == "Frankfurt"


def test_update_roaster(client, auth_headers, db):
    """Test updating roaster data."""
    roaster = Roaster(name="Old Roaster Name", city="Cologne", peru_focus=False)
    db.add(roaster)
    db.commit()
    db.refresh(roaster)

    update_data = {"name": "Updated Roaster Name", "peru_focus": True}
    response = client.patch(
        f"/roasters/{roaster.id}", json=update_data, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Roaster Name"
    assert data["peru_focus"] is True


def test_delete_roaster(client, auth_headers, db):
    """Test deleting a roaster."""
    roaster = Roaster(name="To Delete Roaster", city="Stuttgart")
    db.add(roaster)
    db.commit()
    db.refresh(roaster)

    response = client.delete(f"/roasters/{roaster.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

    # Verify deletion
    response = client.get(f"/roasters/{roaster.id}", headers=auth_headers)
    assert response.status_code == 404


def test_create_roaster_minimal_data(client, auth_headers):
    """Test creating roaster with minimal required data."""
    payload = {"name": "Minimal Roaster"}

    response = client.post("/roasters", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Minimal Roaster"
    assert data["specialty_focus"] is True  # Default value
    assert data["peru_focus"] is False  # Default value


def test_roaster_unauthorized_access(client):
    """Test that accessing roasters without token fails."""
    response = client.get("/roasters")
    assert response.status_code == 401


def test_roaster_viewer_cannot_create(client, viewer_auth_headers):
    """Test that viewer role cannot create roasters."""
    payload = {"name": "Unauthorized Roaster", "city": "Berlin"}

    response = client.post("/roasters", json=payload, headers=viewer_auth_headers)
    assert response.status_code == 403


def test_roaster_viewer_can_read(client, viewer_auth_headers, db):
    """Test that viewer role can read roasters."""
    roaster = Roaster(name="Viewable Roaster", city="Hamburg")
    db.add(roaster)
    db.commit()

    response = client.get("/roasters", headers=viewer_auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_roaster_analyst_can_create(client, analyst_auth_headers):
    """Test that analyst role can create roasters."""
    payload = {"name": "Analyst Created Roaster", "city": "Leipzig"}

    response = client.post("/roasters", json=payload, headers=analyst_auth_headers)
    assert response.status_code == 200


def test_get_nonexistent_roaster(client, auth_headers):
    """Test getting a roaster that doesn't exist."""
    response = client.get("/roasters/99999", headers=auth_headers)
    assert response.status_code == 404


def test_update_nonexistent_roaster(client, auth_headers):
    """Test updating a roaster that doesn't exist."""
    response = client.patch(
        "/roasters/99999", json={"name": "New Name"}, headers=auth_headers
    )
    assert response.status_code == 404


def test_delete_nonexistent_roaster(client, auth_headers):
    """Test deleting a roaster that doesn't exist."""
    response = client.delete("/roasters/99999", headers=auth_headers)
    assert response.status_code == 404
