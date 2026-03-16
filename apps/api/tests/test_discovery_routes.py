def test_discovery_seed_status_success(client, auth_headers, monkeypatch):
    class _Result:
        state = "SUCCESS"
        result = {"created": 3}
        info = None

        def successful(self):
            return True

        def failed(self):
            return False

    monkeypatch.setattr(
        "app.domains.discovery.api.routes.celery.AsyncResult",
        lambda _task_id: _Result(),
    )

    response = client.get("/discovery/seed/task-123", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "SUCCESS"
    assert payload["result"] == {"created": 3}


def test_discovery_seed_status_failure_is_sanitized(client, auth_headers, monkeypatch):
    class _Result:
        state = "FAILURE"
        result = RuntimeError("traceback with secrets")
        info = None

        def successful(self):
            return False

        def failed(self):
            return True

    monkeypatch.setattr(
        "app.domains.discovery.api.routes.celery.AsyncResult",
        lambda _task_id: _Result(),
    )

    response = client.get("/discovery/seed/task-123", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "FAILURE"
    assert payload["error"] == "Discovery task failed"


def test_discovery_seed_status_includes_progress_info(client, auth_headers, monkeypatch):
    class _Result:
        state = "STARTED"
        result = None
        info = {"processed": 4}

        def successful(self):
            return False

        def failed(self):
            return False

    monkeypatch.setattr(
        "app.domains.discovery.api.routes.celery.AsyncResult",
        lambda _task_id: _Result(),
    )

    response = client.get("/discovery/tasks/task-123", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "STARTED"
    assert payload["info"] == {"processed": 4}


def test_discovery_seed_status_rejects_invalid_task_id(client, auth_headers):
    response = client.get("/discovery/seed/task@bad", headers=auth_headers)
    assert response.status_code == 422


def test_discovery_seed_normalizes_country_filter(client, auth_headers, monkeypatch):
    captured_kwargs: dict = {}

    def _fake_send_task(_name, kwargs):
        captured_kwargs.update(kwargs)
        return type("Task", (), {"id": "task-123"})()

    monkeypatch.setattr("app.domains.discovery.api.routes.celery.send_task", _fake_send_task)

    response = client.post(
        "/discovery/seed",
        json={"entity_type": "cooperative", "max_entities": 10, "country_filter": "pe"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert captured_kwargs["country_filter"] == "PE"


def test_discovery_seed_rejects_invalid_country_filter(client, auth_headers):
    response = client.post(
        "/discovery/seed",
        json={"entity_type": "cooperative", "max_entities": 10, "country_filter": "PER"},
        headers=auth_headers,
    )
    assert response.status_code == 422
