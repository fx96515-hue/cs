from __future__ import annotations

import os
import time
import requests

BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:8000")


def wait_for_backend(max_attempts: int = 30, sleep_seconds: int = 1) -> None:
    for attempt in range(max_attempts):
        try:
            health = requests.get(f"{BASE_URL}/health", timeout=2)
            if health.status_code == 200:
                return
        except requests.exceptions.ConnectionError:
            if attempt == max_attempts - 1:
                raise RuntimeError("Backend not ready after 30 attempts")
            time.sleep(sleep_seconds)


def bootstrap_admin() -> None:
    response = requests.post(
        f"{BASE_URL}/auth/dev/bootstrap",
        headers={"Content-Type": "application/json"},
    )
    if response.status_code != 200:
        raise RuntimeError(f"Bootstrap failed: {response.text}")


def login_admin() -> str:
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")
    email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "admin@coffeestudio.com")

    if not password:
        raise RuntimeError("BOOTSTRAP_ADMIN_PASSWORD not set for e2e login")

    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"},
    )
    if response.status_code != 200:
        raise RuntimeError(f"Auth failed: {response.text}")
    return response.json()["access_token"]


def get_auth_token() -> str:
    wait_for_backend()
    bootstrap_admin()
    return login_admin()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
