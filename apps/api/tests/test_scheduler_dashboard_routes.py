from types import SimpleNamespace


def test_scheduler_jobs_endpoint(client, auth_headers):
    response = client.get("/scheduler/jobs", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert any(job["id"].startswith("market_refresh_") for job in data)
    assert all("scheduleHuman" in job for job in data)


def test_scheduler_summary_endpoint(client, auth_headers):
    response = client.get("/scheduler/summary", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 1
    assert data["enabled"] >= 1
    assert "categories" in data


def test_scheduler_run_job_endpoint(client, auth_headers, monkeypatch):
    calls: list[dict] = []

    def fake_send_task(task_name, args=None, kwargs=None):
        calls.append(
            {"task_name": task_name, "args": args or [], "kwargs": kwargs or {}}
        )
        return SimpleNamespace(id="queued-task-123")

    monkeypatch.setattr(
        "app.api.routes.scheduler_dashboard.celery.send_task", fake_send_task
    )

    response = client.post(
        "/scheduler/jobs/market_refresh_01/run", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["task_id"] == "queued-task-123"
    assert calls[0]["task_name"] == "app.workers.tasks.refresh_market"


def test_scheduler_run_unknown_job_returns_404(client, auth_headers):
    response = client.post("/scheduler/jobs/unknown/run", headers=auth_headers)
    assert response.status_code == 404
