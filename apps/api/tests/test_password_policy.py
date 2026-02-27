"""Tests for password policy enforcement."""

from fastapi.testclient import TestClient


def test_password_without_uppercase_rejected(client: TestClient):
    """Test that password without uppercase letter is rejected."""
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "weak1234!"},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("Großbuchstaben" in str(err.get("msg", "")) for err in detail), (
        f"Expected uppercase error, got: {detail}"
    )


def test_password_without_lowercase_rejected(client: TestClient):
    """Test that password without lowercase letter is rejected."""
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "WEAK1234!"},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("Kleinbuchstaben" in str(err.get("msg", "")) for err in detail), (
        f"Expected lowercase error, got: {detail}"
    )


def test_password_without_digit_rejected(client: TestClient):
    """Test that password without digit is rejected."""
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "WeakPass!"},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("Ziffer" in str(err.get("msg", "")) for err in detail), (
        f"Expected digit error, got: {detail}"
    )


def test_password_without_special_char_rejected(client: TestClient):
    """Test that password without special character is rejected."""
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "WeakPass1234"},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("Sonderzeichen" in str(err.get("msg", "")) for err in detail), (
        f"Expected special char error, got: {detail}"
    )


def test_common_password_from_extended_list_rejected(client: TestClient):
    """Test that passwords from extended common list are rejected."""
    common_passwords = [
        "password",
        "12345678",
        "admin123",
        "qwerty",
        "letmein",
        "welcome",
        "administrator",
        "changeme",
        "default",
    ]

    for pwd in common_passwords:
        response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": pwd},
        )
        assert response.status_code == 422, (
            f"Common password '{pwd}' should be rejected"
        )
        detail = response.json()["detail"]
        # Check that it mentions weakness
        assert any("schwach" in str(err.get("msg", "")).lower() for err in detail), (
            f"Expected weak password error for '{pwd}', got: {detail}"
        )


def test_strong_password_accepted(client: TestClient, db):
    """Test that a strong password meeting all criteria is accepted."""
    # Note: This will fail authentication (no such user), but should pass validation
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "StrongP@ss123!"},
    )
    # Should get 401 (invalid credentials), not 422 (validation error)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_password_with_various_special_chars_accepted(client: TestClient):
    """Test that passwords with various special characters are accepted."""
    special_chars_passwords = [
        "TestP@ss1",
        "TestP#ss1",
        "TestP$ss1",
        "TestP%ss1",
        "TestP^ss1",
        "TestP&ss1",
        "TestP*ss1",
        "TestP(ss1)",
        "TestP!ss1",
        "TestP-ss1",
        "TestP_ss1",
        "TestP+ss1",
        "TestP=ss1",
        "TestP[ss]1",
        "TestP{ss}1",
        "TestP|ss1",
        "TestP\\ss1",
        "TestP:ss1",
        "TestP;ss1",
        "TestP'ss1",
        'TestP"ss1',
        "TestP<ss>1",
        "TestP.ss1",
        "TestP,ss1",
        "TestP?ss1",
        "TestP/ss1",
        "TestP`ss1",
        "TestP~ss1",
    ]

    for pwd in special_chars_passwords:
        response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": pwd},
        )
        # Should NOT get 422 (validation error) – getting 401 or 429 both
        # indicate the password passed validation.  429 is possible when the
        # login-endpoint rate limit fires within this test.
        assert response.status_code != 422, (
            f"Password '{pwd}' with special char should pass validation"
        )


def test_password_too_short_rejected(client: TestClient):
    """Test that password shorter than 8 characters is rejected."""
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "Str0ng!"},
    )
    assert response.status_code == 422
    # Should fail on min_length constraint


def test_password_too_long_rejected(client: TestClient):
    """Test that password longer than 128 characters is rejected."""
    long_password = "A1!" + "x" * 126  # 129 characters total
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": long_password},
    )
    assert response.status_code == 422
    # Should fail on max_length constraint
