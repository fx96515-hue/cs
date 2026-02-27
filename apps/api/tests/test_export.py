"""Tests for data export functionality."""

import csv
import io

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_export_cooperatives_csv_unauthorized():
    """Test that export requires authentication."""
    response = client.get("/cooperatives/export/csv")
    assert response.status_code == 401


def test_export_cooperatives_csv_empty(client, auth_headers, db):
    """Test exporting empty cooperatives list."""
    response = client.get("/cooperatives/export/csv", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "filename=" in response.headers.get("content-disposition", "")


def test_export_cooperatives_csv_with_data(client, auth_headers, db):
    """Test exporting cooperatives to CSV."""
    # Create test cooperatives
    coop1_data = {
        "name": "Test Cooperative 1",
        "region": "Cajamarca",
        "contact_email": "test1@example.com",
    }
    coop2_data = {
        "name": "Test Cooperative 2",
        "region": "Cusco",
        "contact_email": "test2@example.com",
    }

    client.post("/cooperatives", json=coop1_data, headers=auth_headers)
    client.post("/cooperatives", json=coop2_data, headers=auth_headers)

    # Export to CSV
    response = client.get("/cooperatives/export/csv", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

    # Parse CSV
    csv_content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["Name"] == "Test Cooperative 1"
    assert rows[0]["Region"] == "Cajamarca"
    assert rows[1]["Name"] == "Test Cooperative 2"
    assert rows[1]["Region"] == "Cusco"


def test_export_roasters_csv_unauthorized():
    """Test that export requires authentication."""
    response = client.get("/roasters/export/csv")
    assert response.status_code == 401


def test_export_roasters_csv_with_data(client, auth_headers, db):
    """Test exporting roasters to CSV."""
    # Create test roasters
    roaster1_data = {
        "name": "Test Roaster 1",
        "city": "Berlin",
        "contact_email": "info@roaster1.de",
    }
    roaster2_data = {
        "name": "Test Roaster 2",
        "city": "Munich",
        "contact_email": "info@roaster2.de",
    }

    client.post("/roasters", json=roaster1_data, headers=auth_headers)
    client.post("/roasters", json=roaster2_data, headers=auth_headers)

    # Export to CSV
    response = client.get("/roasters/export/csv", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

    # Parse CSV
    csv_content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["Name"] == "Test Roaster 1"
    assert rows[0]["City"] == "Berlin"
    assert rows[1]["Name"] == "Test Roaster 2"
    assert rows[1]["City"] == "Munich"


def test_csv_export_includes_headers(client, auth_headers, db):
    """Test that CSV export includes proper headers."""
    # Create a cooperative
    coop_data = {
        "name": "Test Cooperative",
        "region": "Test Region",
    }
    client.post("/cooperatives", json=coop_data, headers=auth_headers)

    # Export to CSV
    response = client.get("/cooperatives/export/csv", headers=auth_headers)
    csv_content = response.content.decode("utf-8")

    # Check headers
    lines = csv_content.split("\n")
    headers = lines[0].split(",")

    assert "ID" in headers[0]
    assert "Name" in headers[1]
    assert "Region" in headers[2]


def test_csv_filename_includes_timestamp(client, auth_headers, db):
    """Test that CSV filename includes timestamp."""
    response = client.get("/cooperatives/export/csv", headers=auth_headers)
    content_disposition = response.headers.get("content-disposition", "")

    assert "cooperatives_export_" in content_disposition
    assert ".csv" in content_disposition
