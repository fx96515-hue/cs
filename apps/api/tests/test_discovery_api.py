from types import SimpleNamespace
from unittest.mock import Mock, patch


def test_discovery_seed_enqueues_standard_mode_by_default(client, auth_headers):
    fake_task = SimpleNamespace(id="task-standard")
    fake_send_task = Mock(return_value=fake_task)

    with patch("app.api.routes.discovery.celery.send_task", fake_send_task):
        response = client.post(
            "/discovery/seed",
            headers=auth_headers,
            json={"entity_type": "cooperative", "max_entities": 5, "dry_run": True},
        )

    assert response.status_code == 200
    assert response.json() == {"task_id": "task-standard", "state": "PENDING"}
    fake_send_task.assert_called_once_with(
        "app.workers.tasks.seed_discovery",
        kwargs={
            "entity_type": "cooperative",
            "mode": "standard",
            "max_entities": 5,
            "dry_run": True,
            "country_filter": None,
        },
    )


def test_discovery_seed_enqueues_deep_mode(client, auth_headers):
    fake_task = SimpleNamespace(id="task-deep")
    fake_send_task = Mock(return_value=fake_task)

    with patch("app.api.routes.discovery.celery.send_task", fake_send_task):
        response = client.post(
            "/discovery/seed",
            headers=auth_headers,
            json={
                "entity_type": "roaster",
                "mode": "deep",
                "max_entities": 3,
                "dry_run": True,
                "country_filter": "DE",
            },
        )

    assert response.status_code == 200
    assert response.json() == {"task_id": "task-deep", "state": "PENDING"}
    fake_send_task.assert_called_once_with(
        "app.workers.tasks.seed_discovery",
        kwargs={
            "entity_type": "roaster",
            "mode": "deep",
            "max_entities": 3,
            "dry_run": True,
            "country_filter": "DE",
        },
    )
