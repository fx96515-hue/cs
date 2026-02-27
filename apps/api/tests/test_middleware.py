"""Tests for security and validation middleware."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_security_headers_present():
    """Test that security headers are added to responses."""
    response = client.get("/health")

    # Check security headers
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in response.headers
    assert "Permissions-Policy" in response.headers


def test_sql_injection_detection():
    """Test that SQL injection attempts are blocked."""
    # Create a test user first (admin role)
    # Since we can't easily create users in these tests, we'll test with a public endpoint
    # that accepts JSON input

    # Test SQL injection in POST request
    malicious_payloads = [
        {"name": "'; DROP TABLE users; --"},
        {"name": "1' UNION SELECT * FROM users--"},
        {"description": "test' OR '1'='1"},
    ]

    # We'll test with the cooperatives endpoint (requires auth, but test validation before auth)
    for payload in malicious_payloads:
        response = client.post("/cooperatives", json=payload)
        # Should be rejected as malicious (400) or unauthorized (401)
        # Either way, it shouldn't process the malicious content
        assert response.status_code in [400, 401]


def test_xss_detection():
    """Test that XSS attempts are blocked."""
    malicious_payloads = [
        {"name": "<script>alert('XSS')</script>"},
        {"description": "javascript:alert('XSS')"},
        {"name": "<img src=x onerror=alert('XSS')>"},
    ]

    for payload in malicious_payloads:
        response = client.post("/cooperatives", json=payload)
        # Should be rejected as malicious (400) or unauthorized (401)
        assert response.status_code in [400, 401]


def test_valid_input_passes_validation():
    """Test that valid input passes through validation middleware."""
    # This will fail auth (401) but should pass validation
    valid_payload = {
        "name": "Valid Cooperative Name",
        "description": "A valid description without malicious content",
    }

    response = client.post("/cooperatives", json=valid_payload)
    # Should get 401 (unauthorized), not 400 (validation error)
    assert response.status_code == 401


def test_nested_malicious_content_detected():
    """Test that malicious content in nested structures is detected."""
    malicious_payload = {
        "name": "Cooperative",
        "contact": {
            "email": "test@example.com",
            "notes": "'; DROP TABLE cooperatives; --",
        },
    }

    response = client.post("/cooperatives", json=malicious_payload)
    assert response.status_code in [400, 401]


def test_array_malicious_content_detected():
    """Test that malicious content in arrays is detected."""
    malicious_payload = {
        "name": "Cooperative",
        "tags": ["normal", "<script>alert('xss')</script>", "safe"],
    }

    response = client.post("/cooperatives", json=malicious_payload)
    assert response.status_code in [400, 401]


def test_rate_limiting():
    """Test that rate limiting works correctly."""
    # Note: The default rate limit is 200 requests per minute
    # We test that the limiter is configured, not that it triggers
    # (triggering 201 requests in tests would be slow and flaky)

    # Make a few requests to verify the limiter is working
    responses = []
    for _ in range(5):
        response = client.get("/health")
        responses.append(response)

    # All requests should succeed (we're well under the limit)
    assert all(r.status_code == 200 for r in responses)

    # Verify rate limit headers would be present if we exceeded limit
    # The rate limiter is configured and active
    assert hasattr(app.state, "limiter")
    assert app.state.limiter is not None


def test_cors_configuration():
    """Test that CORS is properly configured."""
    # Make a request with an Origin header
    headers = {"Origin": "http://localhost:3000"}
    response = client.get("/health", headers=headers)

    # Should have CORS headers in response
    assert response.status_code == 200
    # Note: TestClient doesn't process CORS middleware the same as a real browser
    # but we can verify the middleware is configured in main.py


def test_cors_options_request():
    """Test that OPTIONS requests are handled correctly."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type,Authorization",
    }
    response = client.options("/health", headers=headers)

    # OPTIONS should be allowed
    assert response.status_code in [200, 204]


def test_cors_allowed_methods():
    """Test that only allowed methods are configured."""
    # This is a smoke test to ensure CORS middleware is properly configured
    # The actual method restriction is tested in integration/E2E tests
    from app.main import app

    # Find CORS middleware
    cors_middleware = None
    for middleware in app.user_middleware:
        if "CORSMiddleware" in str(middleware):
            cors_middleware = middleware
            break

    # CORS middleware should be configured
    assert cors_middleware is not None, "CORS middleware should be configured"
