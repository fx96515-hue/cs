"""Boundary tests for quality alerts API routes."""


def test_quality_alerts_rejects_non_positive_acknowledge_id(client, auth_headers):
    response = client.post(
        "/alerts/0/acknowledge",
        json={"acknowledged_by": "test-user"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_quality_alerts_rejects_non_positive_limit(client, auth_headers):
    alerts_response = client.get("/alerts?limit=0", headers=auth_headers)
    assert alerts_response.status_code == 422

    anomalies_response = client.get("/anomalies?limit=0", headers=auth_headers)
    assert anomalies_response.status_code == 422
