"""Tests for CSRF (Cross-Site Request Forgery) protection."""

from fastapi.testclient import TestClient


def test_csrf_token_generation(client: TestClient, auth_headers):
    """Test that CSRF tokens can be generated for authenticated users."""
    response = client.get("/auth/csrf-token", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "csrf_token" in data
    assert len(data["csrf_token"]) > 20  # Token should be substantial length


def test_csrf_token_unique_per_session(client: TestClient, auth_headers):
    """Test that CSRF tokens are unique per session."""
    response1 = client.get("/auth/csrf-token", headers=auth_headers)
    response2 = client.get("/auth/csrf-token", headers=auth_headers)

    assert response1.status_code == 200
    assert response2.status_code == 200

    token1 = response1.json()["csrf_token"]
    token2 = response2.json()["csrf_token"]

    # Tokens should be different for different requests
    # (In this implementation, each call generates a new token)
    assert token1 != token2


def test_csrf_token_requires_authentication(client: TestClient):
    """Test that CSRF token endpoint requires authentication."""
    response = client.get("/auth/csrf-token")

    # Should require authentication
    assert response.status_code == 401


def test_csrf_token_validation_function():
    """Test CSRF token validation functions."""
    from app.core.security import generate_csrf_token, validate_csrf_token

    session_id = "test_user@example.com"

    # Generate token
    token = generate_csrf_token(session_id)
    assert token is not None
    assert len(token) > 20

    # Validate token
    assert validate_csrf_token(session_id, token) is True

    # Wrong token should fail
    assert validate_csrf_token(session_id, "wrong_token") is False

    # Wrong session should fail
    assert validate_csrf_token("wrong_session", token) is False


def test_csrf_token_expiration():
    """Test that CSRF tokens expire after time limit."""
    from app.core.security import generate_csrf_token, validate_csrf_token, _csrf_tokens
    from datetime import datetime, timezone, timedelta

    session_id = "test_expiry@example.com"

    # Generate token
    token = generate_csrf_token(session_id)

    # Manually expire the token
    _csrf_tokens[session_id]["expires"] = datetime.now(timezone.utc) - timedelta(
        hours=1
    )

    # Validation should fail
    assert validate_csrf_token(session_id, token) is False

    # Token should be cleaned up
    assert session_id not in _csrf_tokens


def test_csrf_token_cleanup():
    """Test cleanup of expired CSRF tokens."""
    from app.core.security import (
        generate_csrf_token,
        cleanup_expired_csrf_tokens,
        _csrf_tokens,
    )
    from datetime import datetime, timezone, timedelta

    # Generate some tokens
    session1 = "user1@example.com"
    session2 = "user2@example.com"

    generate_csrf_token(session1)
    generate_csrf_token(session2)

    # Expire first token
    _csrf_tokens[session1]["expires"] = datetime.now(timezone.utc) - timedelta(hours=1)

    # Run cleanup
    cleanup_expired_csrf_tokens()

    # Expired token should be removed
    assert session1 not in _csrf_tokens

    # Valid token should remain
    assert session2 in _csrf_tokens


def test_csrf_protection_documentation():
    """Test that CSRF protection is documented in security module."""
    from app.core import security

    # Check that CSRF functions exist
    assert hasattr(security, "generate_csrf_token")
    assert hasattr(security, "validate_csrf_token")
    assert hasattr(security, "cleanup_expired_csrf_tokens")

    # Check that functions have docstrings
    assert security.generate_csrf_token.__doc__ is not None
    assert security.validate_csrf_token.__doc__ is not None


def test_csrf_token_strength():
    """Test that CSRF tokens are cryptographically strong."""
    from app.core.security import generate_csrf_token

    session_id = "test_strength@example.com"

    # Generate multiple tokens
    tokens = [generate_csrf_token(session_id) for _ in range(10)]

    # All tokens should be unique (highly unlikely to collide with strong RNG)
    assert len(set(tokens)) == len(tokens)

    # Tokens should be URL-safe (no special chars that need encoding)
    for token in tokens:
        assert all(c.isalnum() or c in ["-", "_"] for c in token)
