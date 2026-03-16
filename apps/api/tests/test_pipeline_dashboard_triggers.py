from app.domains.pipeline.api import routes as pipeline_routes


class _DummyRedis:
    def close(self) -> None:
        return None


class _DummyOrchestrator:
    def __init__(self, db, redis_client):
        self.market_runs = 0
        self.intelligence_runs = 0

    def get_circuit_breaker_status(self) -> dict:
        return {}

    def run_full_pipeline(self):
        raise AssertionError("run_full_pipeline should not be called in trigger tests")

    def run_market_pipeline(self) -> None:
        self.market_runs += 1

    def run_intelligence_pipeline(self) -> None:
        self.intelligence_runs += 1


def _patch_pipeline_deps(monkeypatch):
    monkeypatch.setattr(pipeline_routes, "_get_redis", _DummyRedis)
    monkeypatch.setattr(pipeline_routes, "DataPipelineOrchestrator", _DummyOrchestrator)


def test_trigger_market_source_alias(client, auth_headers, monkeypatch):
    _patch_pipeline_deps(monkeypatch)

    response = client.post("/pipeline/trigger/fx%20rates", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["scope"] == "market"


def test_trigger_intelligence_source_alias(client, auth_headers, monkeypatch):
    _patch_pipeline_deps(monkeypatch)

    response = client.post("/pipeline/trigger/market%20news", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["scope"] == "intelligence"


def test_trigger_unknown_source_returns_404(client, auth_headers, monkeypatch):
    _patch_pipeline_deps(monkeypatch)

    response = client.post("/pipeline/trigger/unknown", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown pipeline source"


def test_trigger_source_rejects_invalid_characters(client, auth_headers):
    response = client.post("/pipeline/trigger/market@news", headers=auth_headers)
    assert response.status_code == 422

