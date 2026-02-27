"""
Integration tests for Peru sourcing intelligence API endpoints.

Tests the full API flow including region intelligence and cooperative analysis.
"""

from app.models.cooperative import Cooperative


def test_list_peru_regions_empty(client, auth_headers, db):
    """Test listing regions when none exist."""
    response = client.get("/peru/regions", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_seed_peru_regions(client, auth_headers, db):
    """Test seeding Peru regions."""
    response = client.post("/peru/regions/seed", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_regions"] == 6
    assert len(data["regions"]) == 6
    assert "Cajamarca" in data["regions"]
    assert "Junín" in data["regions"]


def test_list_peru_regions_after_seed(client, auth_headers, db):
    """Test listing regions after seeding."""
    # Seed first
    client.post("/peru/regions/seed", headers=auth_headers)

    # Now list
    response = client.get("/peru/regions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6
    assert all("name" in r for r in data)
    assert all("country" in r for r in data)
    assert all(r["country"] == "Peru" for r in data)


def test_get_region_intelligence(client, auth_headers, db):
    """Test getting region intelligence."""
    # Seed first
    client.post("/peru/regions/seed", headers=auth_headers)

    # Get Cajamarca intelligence
    response = client.get("/peru/regions/Cajamarca/intelligence", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Cajamarca"
    assert data["country"] == "Peru"
    assert "elevation_range" in data
    assert "climate" in data
    assert "production" in data
    assert "quality" in data
    assert "logistics" in data
    assert "risks" in data
    assert "scores" in data


def test_get_region_intelligence_not_found(client, auth_headers, db):
    """Test getting intelligence for non-existent region."""
    response = client.get(
        "/peru/regions/NonExistent/intelligence", headers=auth_headers
    )
    assert response.status_code == 404
    # Check if response is JSON and has detail field
    try:
        data = response.json()
        if "detail" in data:
            assert "not found" in data["detail"].lower()
    except Exception:
        # Response might not be JSON, just check status code
        pass


def test_analyze_cooperative_not_found(client, auth_headers, db):
    """Test analyzing non-existent cooperative."""
    response = client.post("/peru/cooperatives/99999/analyze", headers=auth_headers)
    assert response.status_code == 404


def test_analyze_cooperative_success(client, auth_headers, db):
    """Test successful cooperative analysis."""
    # Create a cooperative with complete data
    coop = Cooperative(
        name="Test Analysis Coop",
        region="Cajamarca",
        quality_score=80,
        operational_data={
            "annual_volume_kg": 100000,
            "farmer_count": 500,
            "storage_capacity_kg": 200000,
            "processing_facilities": ["wet_mill", "dry_mill"],
            "years_exporting": 10,
        },
        export_readiness={
            "has_export_license": True,
            "license_expiry_date": "2026-12-31",
            "senasa_registered": True,
            "certifications": ["Organic", "Fair Trade", "Rainforest Alliance"],
            "customs_issues_count": 0,
            "has_document_coordinator": True,
        },
        financial_data={"fob_price_per_kg": 4.85, "annual_revenue_usd": 500000},
        communication_metrics={
            "avg_response_hours": 24,
            "languages": ["Spanish", "English"],
            "missed_meetings": 0,
        },
        digital_footprint={
            "has_website": True,
            "has_facebook": True,
            "has_instagram": True,
            "has_whatsapp": True,
            "has_photos": True,
            "has_cupping_scores": True,
        },
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    # Analyze
    response = client.post(
        f"/peru/cooperatives/{coop.id}/analyze", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert data["cooperative_id"] == coop.id
    assert data["cooperative_name"] == "Test Analysis Coop"
    assert "supply_capacity" in data
    assert "export_readiness" in data
    assert "communication_quality" in data
    assert "price_benchmark" in data
    assert "risk_assessment" in data
    assert "scores" in data
    assert "recommendation" in data

    # Verify scores
    assert data["scores"]["supply_capacity"] == 100  # Perfect score
    assert data["scores"]["export_readiness"] == 100  # Perfect score
    assert data["scores"]["total"] > 80  # Should be high

    # Verify recommendation
    assert data["recommendation"]["level"] in ["HIGHLY RECOMMENDED", "RECOMMENDED"]


def test_get_cached_analysis(client, auth_headers, db):
    """Test getting cached analysis results."""
    # Create cooperative
    coop = Cooperative(
        name="Cached Analysis Coop",
        region="Junín",
        quality_score=75,
        operational_data={"annual_volume_kg": 50000},
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    # First analysis (creates cache)
    response1 = client.post(
        f"/peru/cooperatives/{coop.id}/analyze", headers=auth_headers
    )
    assert response1.status_code == 200

    # Get cached result
    response2 = client.get(
        f"/peru/cooperatives/{coop.id}/sourcing-analysis", headers=auth_headers
    )
    assert response2.status_code == 200

    # Results should be identical
    assert response1.json()["analyzed_at"] == response2.json()["analyzed_at"]


def test_refresh_region_data(client, auth_headers, db):
    """Test refreshing region data from external sources."""
    response = client.post(
        "/peru/regions/refresh", json={"region_name": "Cajamarca"}, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["region"] == "Cajamarca"
    assert data["refreshed"] is True
    assert "sources" in data
