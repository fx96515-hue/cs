"""Tests for security utilities."""

import pytest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)
from jose import JWTError


def test_hash_password():
    """Test password hashing."""
    password = "test_password_123"
    hashed = hash_password(password)

    assert hashed != password
    assert len(hashed) > 0
    # Verify argon2id variant with OWASP-recommended parameters
    assert "$argon2id$v=19$m=65536,t=3,p=4$" in hashed


def test_verify_password_correct():
    """Test password verification with correct password."""
    password = "test_password_123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    """Test password verification with incorrect password."""
    password = "test_password_123"
    wrong_password = "wrong_password"
    hashed = hash_password(password)

    assert verify_password(wrong_password, hashed) is False


def test_create_access_token():
    """Test JWT token creation."""
    token = create_access_token(sub="test@example.com", role="admin")

    assert isinstance(token, str)
    assert len(token) > 0

    # Should be decodable
    decoded = decode_token(token)
    assert decoded["sub"] == "test@example.com"
    assert decoded["role"] == "admin"


def test_create_access_token_custom_expiry():
    """Test JWT token creation with custom expiry."""
    token = create_access_token(
        sub="test@example.com", role="admin", expires_minutes=30
    )

    assert isinstance(token, str)
    decoded = decode_token(token)
    assert decoded["sub"] == "test@example.com"


def test_decode_token_valid():
    """Test decoding a valid token."""
    token = create_access_token(sub="test@example.com", role="admin")
    decoded = decode_token(token)

    assert "sub" in decoded
    assert "role" in decoded
    assert "iss" in decoded
    assert "aud" in decoded
    assert "exp" in decoded


def test_decode_token_invalid():
    """Test decoding an invalid token."""
    invalid_token = "invalid.token.here"

    with pytest.raises(JWTError):
        decode_token(invalid_token)


def test_hash_password_different_each_time():
    """Test that hashing same password produces different hashes."""
    password = "test_password_123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    # Hashes should be different due to salt
    assert hash1 != hash2

    # But both should verify
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_token_contains_required_claims():
    """Test that token contains all required claims."""
    token = create_access_token(sub="test@example.com", role="analyst")
    decoded = decode_token(token)

    required_claims = ["sub", "role", "iss", "aud", "iat", "exp"]
    for claim in required_claims:
        assert claim in decoded


def test_hash_empty_password():
    """Test hashing an empty password."""
    password = ""
    hashed = hash_password(password)

    assert len(hashed) > 0
    assert verify_password(password, hashed) is True


def test_different_roles_in_tokens():
    """Test creating tokens with different roles."""
    roles = ["admin", "analyst", "viewer"]

    for role in roles:
        token = create_access_token(sub="test@example.com", role=role)
        decoded = decode_token(token)
        assert decoded["role"] == role


def test_backward_compatibility_pbkdf2():
    """Test that old pbkdf2 hashes can still be verified."""
    from passlib.context import CryptContext

    # Simulate an old pbkdf2 hash (like what existed before argon2 migration)
    old_context = CryptContext(
        schemes=["pbkdf2_sha256"], deprecated="auto", pbkdf2_sha256__rounds=300000
    )
    password = "legacy_password"
    old_hash = old_context.hash(password)

    # Verify that the new hash_password context can still verify old hashes
    assert verify_password(password, old_hash) is True
    assert verify_password("wrong_password", old_hash) is False
