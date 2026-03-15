"""Tests for health and readiness endpoints."""


class _DummyRedisClient:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.closed = False

    def ping(self):
        if self.should_fail:
            raise RuntimeError("redis stack trace should never leak")

    def close(self):
        self.closed = True


def test_ready_returns_200_when_db_and_redis_are_ok(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.health.redis_lib.from_url",
        lambda *args, **kwargs: _DummyRedisClient(should_fail=False),
    )

    response = client.get("/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["services"]["database"] == "ok"
    assert payload["services"]["redis"] == "ok"


def test_ready_redacts_dependency_errors(client, db, monkeypatch):
    def _db_failure(*args, **kwargs):
        raise RuntimeError("db secret details")

    monkeypatch.setattr(db, "execute", _db_failure)
    monkeypatch.setattr(
        "app.api.routes.health.redis_lib.from_url",
        lambda *args, **kwargs: _DummyRedisClient(should_fail=True),
    )

    response = client.get("/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["services"]["database"] == "error"
    assert payload["services"]["redis"] == "error"
    assert "secret" not in str(payload)


def test_health_db_success(client):
    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "database"}


def test_health_db_failure_returns_sanitized_error(client, db, monkeypatch):
    def _db_failure(*args, **kwargs):
        raise RuntimeError("db secret details")

    monkeypatch.setattr(db, "execute", _db_failure)

    response = client.get("/health/db")
    assert response.status_code == 503
    assert response.json()["detail"] == "Database health check failed"


def test_health_redis_success(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.health.redis_lib.from_url",
        lambda *args, **kwargs: _DummyRedisClient(should_fail=False),
    )

    response = client.get("/health/redis")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "redis"}


def test_health_redis_failure_returns_sanitized_error(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.health.redis_lib.from_url",
        lambda *args, **kwargs: _DummyRedisClient(should_fail=True),
    )

    response = client.get("/health/redis")
    assert response.status_code == 503
    assert response.json()["detail"] == "Redis health check failed"
