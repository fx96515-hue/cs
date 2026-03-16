"""API-level tests for ML training route error handling."""


def test_train_model_value_error_is_sanitized(client, auth_headers, monkeypatch):
    def _raise_value_error(*args, **kwargs):
        raise ValueError("sensitive training internals")

    monkeypatch.setattr(
        "app.domains.ml_training.api.routes.train_freight_model", _raise_value_error
    )

    response = client.post("/ml/train/train/freight_cost", headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid training request"


def test_train_model_runtime_error_is_sanitized(client, auth_headers, monkeypatch):
    def _raise_runtime_error(*args, **kwargs):
        raise RuntimeError("traceback and secrets")

    monkeypatch.setattr(
        "app.domains.ml_training.api.routes.train_freight_model", _raise_runtime_error
    )

    response = client.post("/ml/train/train/freight_cost", headers=auth_headers)
    assert response.status_code == 500
    assert response.json()["detail"] == "Training failed"


def test_train_model_rejects_invalid_model_type(client, auth_headers):
    response = client.post("/ml/train/train/invalid", headers=auth_headers)
    assert response.status_code == 422


def test_training_status_rejects_invalid_model_type_filter(client, auth_headers):
    response = client.get(
        "/ml/train/training-status?model_type=invalid",
        headers=auth_headers,
    )
    assert response.status_code == 422
