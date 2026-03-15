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
        "app.api.routes.discovery.celery.AsyncResult",
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
        "app.api.routes.discovery.celery.AsyncResult",
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
        "app.api.routes.discovery.celery.AsyncResult",
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
