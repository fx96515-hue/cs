"""Tests for SQL injection protection."""

from fastapi.testclient import TestClient


def test_sql_injection_in_cooperative_name(client: TestClient, auth_headers):
    """Test that SQL injection attempts in cooperative names are rejected."""
    malicious_payloads = [
        "'; DROP TABLE cooperatives; --",
        "1' OR '1'='1",
        "admin' --",
        "'; DELETE FROM users WHERE '1'='1",
        "1' UNION SELECT * FROM users --",
    ]

    for payload in malicious_payloads:
        response = client.post(
            "/cooperatives/",
            headers=auth_headers,
            json={"name": payload, "region": "Cajamarca"},
        )
        # Should be rejected by middleware or Pydantic validation
        assert response.status_code in [400, 422], f"Payload not rejected: {payload}"


def test_sql_injection_in_roaster_name(client: TestClient, auth_headers):
    """Test that SQL injection attempts in roaster names are rejected."""
    malicious_payloads = [
        "' OR 1=1; --",
        "'; SELECT * FROM users; --",
        "1' UNION SELECT NULL, NULL, NULL --",
    ]

    for payload in malicious_payloads:
        response = client.post(
            "/roasters/", headers=auth_headers, json={"name": payload, "city": "Berlin"}
        )
        # Should be rejected by middleware or Pydantic validation
        assert response.status_code in [400, 422], f"Payload not rejected: {payload}"


def test_sql_injection_in_lot_name(client: TestClient, auth_headers, db):
    """Test that SQL injection attempts in lot names are rejected."""
    # First create a cooperative
    from app.models.cooperative import Cooperative

    coop = Cooperative(name="Test Coop", region="Cajamarca")
    db.add(coop)
    db.commit()

    malicious_payloads = [
        "'; DROP TABLE lots; --",
        "1' OR '1'='1",
    ]

    for payload in malicious_payloads:
        response = client.post(
            "/lots/",
            headers=auth_headers,
            json={
                "cooperative_id": coop.id,
                "name": payload,
            },
        )
        # Should be rejected by middleware or Pydantic validation
        assert response.status_code in [400, 422], f"Payload not rejected: {payload}"


def test_orm_queries_safe_from_injection(client: TestClient, auth_headers, db):
    """Test that ORM queries with user input are safe."""
    # Create a cooperative with a safe name
    from app.models.cooperative import Cooperative

    coop = Cooperative(name="Safe Cooperative", region="Cajamarca")
    db.add(coop)
    db.commit()

    # Try to retrieve it with various "malicious" query attempts
    # These should all fail to return unexpected results
    response = client.get(f"/cooperatives/{coop.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Safe Cooperative"

    # Try with non-existent ID (simulating injection attempt)
    response = client.get("/cooperatives/999999", headers=auth_headers)
    assert response.status_code == 404


def test_complex_sql_injection_patterns(client: TestClient, auth_headers):
    """Test more complex SQL injection patterns."""
    complex_payloads = [
        "1'; EXEC sp_MSForEachTable 'DROP TABLE ?'; --",
        "1' AND (SELECT COUNT(*) FROM users) > 0 --",
        "1' WAITFOR DELAY '00:00:05' --",
        "1'; SHUTDOWN; --",
    ]

    for payload in complex_payloads:
        response = client.post(
            "/cooperatives/",
            headers=auth_headers,
            json={"name": payload, "region": "Cajamarca"},
        )
        # Should be rejected
        assert response.status_code in [
            400,
            422,
        ], f"Complex payload not rejected: {payload}"


def test_blind_sql_injection_time_based(client: TestClient, auth_headers):
    """Test that time-based blind SQL injection attempts are blocked."""
    import time

    payload = "test' OR (SELECT SLEEP(5)) --"
    start_time = time.time()

    response = client.post(
        "/cooperatives/",
        headers=auth_headers,
        json={"name": payload, "region": "Cajamarca"},
    )

    elapsed_time = time.time() - start_time

    # Should be rejected quickly, not delay for 5 seconds
    assert elapsed_time < 2, "Possible time-based SQL injection vulnerability"
    assert response.status_code in [400, 422]
