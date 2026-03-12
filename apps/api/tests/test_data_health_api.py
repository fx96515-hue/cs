"""Tests for data health routes with error sanitization."""

from datetime import datetime, timezone
from types import SimpleNamespace

from app.api.routes import data_health as data_health_routes


class _DummyRedis:
    def close(self) -> None:
        return None


class _DummyBreaker:
    def __init__(self, state: str = "open"):
        self._state = state

    def get_status(self) -> dict:
        return {"state": self._state}

    def reset(self) -> None:
        self._state = "closed"


class _DummyOrchestrator:
    def __init__(self, db, redis_client):
        self.breakers = {"news": _DummyBreaker("open")}

    def get_circuit_breaker_status(self) -> dict:
        return {"news": {"state": "open"}}

    def run_full_pipeline(self):
        now = datetime.now(timezone.utc)
        return SimpleNamespace(
            status="partial",
            duration_seconds=1.23,
            operations={
                "market": {"status": "failed", "errors": ["secret details"]},
                "intelligence": {"status": "partial"},
            },
            errors=["traceback details", "database failure"],
            started_at=now,
            completed_at=now,
        )

    def run_market_pipeline(self) -> dict:
        return {
            "status": "partial",
            "duration_seconds": 0.42,
            "results": {
                "fx_rates": {
                    "success": False,
                    "error": "internal stack trace",
                    "errors": ["first", "second"],
                }
            },
            "errors": ["market pipeline exploded"],
        }

    def run_intelligence_pipeline(self) -> dict:
        return {
            "status": "partial",
            "duration_seconds": 0.55,
            "results": {
                "news": {
                    "success": False,
                    "exception": "traceback text",
                    "traceback": "sensitive traceback",
                }
            },
            "errors": ["intel pipeline exploded"],
        }


def _patch_data_health_deps(monkeypatch):
    monkeypatch.setattr(data_health_routes, "_get_redis", _DummyRedis)
    monkeypatch.setattr(
        data_health_routes, "DataPipelineOrchestrator", _DummyOrchestrator
    )


def test_refresh_market_redacts_internal_errors(client, auth_headers, monkeypatch):
    _patch_data_health_deps(monkeypatch)

    response = client.post("/data-health/refresh-market", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["errors"] == []
    assert payload["sources"] == []


def test_refresh_intelligence_redacts_internal_errors(
    client, auth_headers, monkeypatch
):
    _patch_data_health_deps(monkeypatch)

    response = client.post("/data-health/refresh-intelligence", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["errors"] == []
    assert payload["sources"] == []


def test_refresh_all_redacts_top_level_errors(client, auth_headers, monkeypatch):
    _patch_data_health_deps(monkeypatch)

    response = client.post("/data-health/refresh-all", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "partial"
    assert payload["errors"] == [
        "Pipeline operation failed",
        "Pipeline operation failed",
    ]


def test_reset_circuit_unknown_provider_returns_safe_response(
    client, auth_headers, monkeypatch
):
    _patch_data_health_deps(monkeypatch)

    response = client.post("/data-health/reset-circuit/unknown", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] == "Unknown provider: unknown"
    assert "available_providers" in payload
