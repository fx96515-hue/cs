"""API-level tests for auto-outreach error handling."""


def test_create_campaign_value_error_returns_400(client, auth_headers, monkeypatch):
    def _raise_value_error(*args, **kwargs):
        raise ValueError("invalid campaign config")

    monkeypatch.setattr(
        "app.api.routes.auto_outreach.auto_outreach.create_campaign",
        _raise_value_error,
    )

    response = client.post(
        "/auto-outreach/campaign",
        json={"name": "Campaign", "entity_type": "cooperative"},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid request"


def test_create_campaign_runtime_error_returns_500(client, auth_headers, monkeypatch):
    def _raise_runtime_error(*args, **kwargs):
        raise RuntimeError("internal traceback")

    monkeypatch.setattr(
        "app.api.routes.auto_outreach.auto_outreach.create_campaign",
        _raise_runtime_error,
    )

    response = client.post(
        "/auto-outreach/campaign",
        json={"name": "Campaign", "entity_type": "cooperative"},
        headers=auth_headers,
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Campaign creation failed"


def test_get_suggestions_runtime_error_returns_500(client, auth_headers, monkeypatch):
    def _raise_runtime_error(*args, **kwargs):
        raise RuntimeError("internal traceback")

    monkeypatch.setattr(
        "app.api.routes.auto_outreach.auto_outreach.get_outreach_suggestions",
        _raise_runtime_error,
    )

    response = client.get(
        "/auto-outreach/suggestions?entity_type=cooperative&limit=1",
        headers=auth_headers,
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to get outreach suggestions"


def test_get_entity_status_runtime_error_returns_500(client, auth_headers, monkeypatch):
    def _raise_runtime_error(*args, **kwargs):
        raise RuntimeError("internal traceback")

    monkeypatch.setattr(
        "app.api.routes.auto_outreach.auto_outreach.get_entity_outreach_status",
        _raise_runtime_error,
    )

    response = client.get(
        "/auto-outreach/status/cooperative/1",
        headers=auth_headers,
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to get entity outreach status"
