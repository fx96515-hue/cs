from app.models.user import User
from app.core.security import hash_password


def test_login_success(client, test_user):
    """Test successful login with valid credentials."""
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "TestP@ss123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_sets_http_only_auth_cookie(client, test_user):
    """Successful logins must establish an HttpOnly cookie-backed session."""
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "TestP@ss123!"}
    )
    assert response.status_code == 200
    set_cookie = response.headers.get("set-cookie", "")
    assert "coffeestudio_access_token=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie


def test_login_invalid_password(client, test_user):
    """Test login with invalid password."""
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "WrongP@ss123!"}
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert "Invalid credentials" in data["error"]["message"]


def test_login_invalid_email(client):
    """Test login with non-existent email."""
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "AnyP@ss123!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert "Invalid credentials" in data["error"]["message"]


def test_login_email_case_insensitive(client, test_user):
    """Login should accept mixed-case emails and match users case-insensitively."""
    response = client.post(
        "/auth/login",
        json={"email": "Test@Example.Com", "password": "TestP@ss123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_inactive_user(client, db):
    """Test login with inactive user account."""
    inactive_user = User(
        email="inactive@example.com",
        password_hash=hash_password("InactiveP@ss123!"),
        role="admin",
        is_active=False,
    )
    db.add(inactive_user)
    db.commit()

    response = client.post(
        "/auth/login",
        json={"email": "inactive@example.com", "password": "InactiveP@ss123!"},
    )
    assert response.status_code == 401


def test_get_current_user(client, auth_headers, test_user):
    """Test getting current user information."""
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["role"] == test_user.role
    assert data["is_active"] is True


def test_get_current_user_with_cookie_auth(client, test_user):
    """Protected routes must also work with the secure auth cookie."""
    login_response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "TestP@ss123!"}
    )
    assert login_response.status_code == 200

    response = client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email


def test_logout_clears_auth_cookie(client, test_user):
    """Logout should explicitly clear the auth cookie."""
    login_response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "TestP@ss123!"}
    )
    assert login_response.status_code == 200

    logout_response = client.post("/auth/logout")
    assert logout_response.status_code == 204

    cleared_cookie = logout_response.headers.get("set-cookie", "")
    assert "coffeestudio_access_token=" in cleared_cookie
    assert "Max-Age=0" in cleared_cookie or "expires=" in cleared_cookie.lower()

    me_response = client.get("/auth/me")
    assert me_response.status_code == 401


def test_refresh_renews_auth_cookie(client, test_user):
    """Refresh should continue the cookie-backed session without exposing persistence in JS."""
    login_response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "TestP@ss123!"}
    )
    assert login_response.status_code == 200

    refresh_response = client.post("/auth/refresh")
    assert refresh_response.status_code == 200
    refresh_cookie = refresh_response.headers.get("set-cookie", "")
    assert "coffeestudio_access_token=" in refresh_cookie
    assert "HttpOnly" in refresh_cookie


def test_protected_route_without_token(client):
    """Test accessing protected route without authentication token."""
    response = client.get("/cooperatives")
    assert response.status_code == 401


def test_protected_route_with_invalid_token(client):
    """Test accessing protected route with invalid token."""
    headers = {"Authorization": "Bearer invalid_token_here"}
    response = client.get("/cooperatives", headers=headers)
    assert response.status_code == 401


def test_protected_route_with_malformed_token(client):
    """Test accessing protected route with malformed token."""
    headers = {"Authorization": "InvalidFormat"}
    response = client.get("/cooperatives", headers=headers)
    assert response.status_code == 401


def test_token_contains_user_info(client, test_user):
    """Test that login token contains correct user information."""
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "TestP@ss123!"}
    )
    assert response.status_code == 200

    # Use the token to get user info
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user_response = client.get("/auth/me", headers=headers)
    assert user_response.status_code == 200
    assert user_response.json()["email"] == "test@example.com"


def test_different_user_roles_have_access(client, analyst_auth_headers):
    """Test that different roles can login and access appropriate resources."""
    # Analyst can view cooperatives
    coop_response = client.get("/cooperatives", headers=analyst_auth_headers)
    assert coop_response.status_code == 200


def test_viewer_role_restrictions(client, viewer_auth_headers):
    """Test that viewer role has restricted access."""
    # Viewer can read
    read_response = client.get("/cooperatives", headers=viewer_auth_headers)
    assert read_response.status_code == 200

    # Viewer cannot create
    create_response = client.post(
        "/cooperatives", json={"name": "Test"}, headers=viewer_auth_headers
    )
    assert create_response.status_code == 403


def test_login_missing_email(client):
    """Test login with missing email field."""
    response = client.post("/auth/login", json={"password": "TestP@ss123!"})
    assert response.status_code == 422  # Validation error


def test_login_missing_password(client):
    """Test login with missing password field."""
    response = client.post("/auth/login", json={"email": "test@example.com"})
    assert response.status_code == 422  # Validation error


def test_login_empty_credentials(client):
    """Test login with empty credentials."""
    response = client.post("/auth/login", json={"email": "", "password": ""})
    assert response.status_code == 422  # Validation error
