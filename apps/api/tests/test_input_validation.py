"""Tests for input validation across all schemas."""

from fastapi.testclient import TestClient


class TestCooperativeValidation:
    """Tests for Cooperative schema validation."""

    def test_valid_cooperative_creation(self, client: TestClient, auth_headers):
        """Test that valid cooperative data is accepted."""
        response = client.post(
            "/cooperatives/",
            headers=auth_headers,
            json={
                "name": "Test Cooperative",
                "region": "Cajamarca",
                "altitude_m": 1500,
                "contact_email": "contact@example.com",
                "website": "https://example.com",
            },
        )
        assert response.status_code == 200

    def test_cooperative_name_too_short(self, client: TestClient, auth_headers):
        """Test that too-short names are rejected."""
        response = client.post(
            "/cooperatives/",
            headers=auth_headers,
            json={"name": "X", "region": "Cajamarca"},
        )
        assert response.status_code == 422

    def test_cooperative_altitude_validation(self, client: TestClient, auth_headers):
        """Test altitude range validation."""
        # Test negative altitude
        response = client.post(
            "/cooperatives/",
            headers=auth_headers,
            json={"name": "Test Coop", "altitude_m": -100},
        )
        assert response.status_code == 422

        # Test altitude too high
        response = client.post(
            "/cooperatives/",
            headers=auth_headers,
            json={"name": "Test Coop", "altitude_m": 7000},
        )
        assert response.status_code == 422

    def test_cooperative_email_validation(self, client: TestClient, auth_headers):
        """Test email format validation."""
        invalid_emails = ["notanemail", "missing@domain", "@nodomain.com"]

        for email in invalid_emails:
            response = client.post(
                "/cooperatives/",
                headers=auth_headers,
                json={"name": "Test Coop", "contact_email": email},
            )
            assert response.status_code == 422

    def test_cooperative_website_validation(self, client: TestClient, auth_headers):
        """Test website URL validation."""
        # Invalid URLs
        invalid_urls = ["notaurl", "ftp://example.com", "javascript:void(0)"]

        for url in invalid_urls:
            response = client.post(
                "/cooperatives/",
                headers=auth_headers,
                json={"name": "Test Coop", "website": url},
            )
            # Can be rejected by middleware (400) or Pydantic validation (422)
            assert response.status_code in [
                400,
                422,
            ], f"Invalid URL not rejected: {url}"


class TestLotValidation:
    """Tests for Lot schema validation."""

    def test_lot_cooperative_id_required(self, client: TestClient, auth_headers):
        """Test that cooperative_id is required and positive."""
        response = client.post(
            "/lots/",
            headers=auth_headers,
            json={"name": "Test Lot", "cooperative_id": 0},
        )
        assert response.status_code == 422

    def test_lot_name_validation(self, client: TestClient, auth_headers, db):
        """Test lot name validation."""
        from app.models.cooperative import Cooperative

        coop = Cooperative(name="Test Coop", region="Cajamarca")
        db.add(coop)
        db.commit()

        # Too short
        response = client.post(
            "/lots/",
            headers=auth_headers,
            json={"name": "X", "cooperative_id": coop.id},
        )
        assert response.status_code == 422

    def test_lot_crop_year_validation(self, client: TestClient, auth_headers, db):
        """Test crop year range validation."""
        from app.models.cooperative import Cooperative

        coop = Cooperative(name="Test Coop", region="Cajamarca")
        db.add(coop)
        db.commit()

        # Invalid year (too old)
        response = client.post(
            "/lots/",
            headers=auth_headers,
            json={"name": "Test Lot", "cooperative_id": coop.id, "crop_year": 1999},
        )
        assert response.status_code == 422

        # Invalid year (too future)
        response = client.post(
            "/lots/",
            headers=auth_headers,
            json={"name": "Test Lot", "cooperative_id": coop.id, "crop_year": 2101},
        )
        assert response.status_code == 422

    def test_lot_incoterm_validation(self, client: TestClient, auth_headers, db):
        """Test incoterm validation."""
        from app.models.cooperative import Cooperative

        coop = Cooperative(name="Test Coop", region="Cajamarca")
        db.add(coop)
        db.commit()

        # Invalid incoterm
        response = client.post(
            "/lots/",
            headers=auth_headers,
            json={"name": "Test Lot", "cooperative_id": coop.id, "incoterm": "INVALID"},
        )
        assert response.status_code == 422

        # Valid incoterm
        response = client.post(
            "/lots/",
            headers=auth_headers,
            json={"name": "Test Lot", "cooperative_id": coop.id, "incoterm": "FOB"},
        )
        assert response.status_code == 200

    def test_lot_price_validation(self, client: TestClient, auth_headers, db):
        """Test price validation."""
        from app.models.cooperative import Cooperative

        coop = Cooperative(name="Test Coop", region="Cajamarca")
        db.add(coop)
        db.commit()

        # Negative price
        response = client.post(
            "/lots/",
            headers=auth_headers,
            json={"name": "Test Lot", "cooperative_id": coop.id, "price_per_kg": -5},
        )
        assert response.status_code == 422

        # Unreasonably high price
        response = client.post(
            "/lots/",
            headers=auth_headers,
            json={"name": "Test Lot", "cooperative_id": coop.id, "price_per_kg": 50000},
        )
        assert response.status_code == 422


class TestRoasterValidation:
    """Tests for Roaster schema validation."""

    def test_roaster_price_position_validation(self, client: TestClient, auth_headers):
        """Test price position enum validation."""
        # Invalid price position
        response = client.post(
            "/roasters/",
            headers=auth_headers,
            json={"name": "Test Roaster", "price_position": "invalid"},
        )
        assert response.status_code == 422

        # Valid price position
        for position in ["premium", "mid-range", "value", "luxury"]:
            response = client.post(
                "/roasters/",
                headers=auth_headers,
                json={"name": f"Test Roaster {position}", "price_position": position},
            )
            assert response.status_code == 200

    def test_roaster_email_validation(self, client: TestClient, auth_headers):
        """Test roaster email validation."""
        response = client.post(
            "/roasters/",
            headers=auth_headers,
            json={"name": "Test Roaster", "contact_email": "invalid-email"},
        )
        assert response.status_code == 422


class TestCuppingValidation:
    """Tests for Cupping schema validation."""

    def test_cupping_score_ranges(self, client: TestClient, auth_headers):
        """Test that cupping scores are within valid ranges."""
        # SCA score out of range
        response = client.post(
            "/cuppings/", headers=auth_headers, json={"sca_score": 150}
        )
        assert response.status_code == 422

        # Component score out of range
        response = client.post("/cuppings/", headers=auth_headers, json={"aroma": 15})
        assert response.status_code == 422


class TestLogisticsValidation:
    """Tests for Logistics schema validation."""

    def test_landed_cost_weight_validation(self, client: TestClient, auth_headers):
        """Test weight validation in landed cost calculator."""
        # Negative weight
        response = client.post(
            "/logistics/landed-cost",
            headers=auth_headers,
            json={"weight_kg": -100, "green_price_usd_per_kg": 5.0},
        )
        assert response.status_code == 422

        # Zero weight
        response = client.post(
            "/logistics/landed-cost",
            headers=auth_headers,
            json={"weight_kg": 0, "green_price_usd_per_kg": 5.0},
        )
        assert response.status_code == 422


class TestMarginValidation:
    """Tests for Margin calculation schema validation."""

    def test_margin_currency_validation(self, client: TestClient, auth_headers):
        """Test currency validation in margin calculator."""
        # Invalid currency
        response = client.post(
            "/margins/calc",
            headers=auth_headers,
            json={"purchase_price_per_kg": 5.0, "purchase_currency": "INVALID"},
        )
        assert response.status_code == 422

    def test_margin_yield_factor_validation(self, client: TestClient, auth_headers):
        """Test yield factor validation."""
        # Yield factor > 1
        response = client.post(
            "/margins/calc",
            headers=auth_headers,
            json={"purchase_price_per_kg": 5.0, "yield_factor": 1.5},
        )
        assert response.status_code == 422

        # Yield factor <= 0
        response = client.post(
            "/margins/calc",
            headers=auth_headers,
            json={"purchase_price_per_kg": 5.0, "yield_factor": 0},
        )
        assert response.status_code == 422
