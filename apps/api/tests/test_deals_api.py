"""Boundary tests for deals API routes."""


def test_deals_reject_non_positive_path_ids(client, auth_headers):
    response_get = client.get("/deals/0", headers=auth_headers)
    assert response_get.status_code == 422

    response_patch = client.patch("/deals/0", json={"status": "open"}, headers=auth_headers)
    assert response_patch.status_code == 422

    response_delete = client.delete("/deals/0", headers=auth_headers)
    assert response_delete.status_code == 422

    response_restore = client.post("/deals/0/restore", headers=auth_headers)
    assert response_restore.status_code == 422


def test_deals_reject_non_positive_filter_ids(client, auth_headers):
    response_coop = client.get("/deals?cooperative_id=0", headers=auth_headers)
    assert response_coop.status_code == 422

    response_roaster = client.get("/deals?roaster_id=0", headers=auth_headers)
    assert response_roaster.status_code == 422

    response_lot = client.get("/deals?lot_id=0", headers=auth_headers)
    assert response_lot.status_code == 422


def test_deals_reject_invalid_status_filter(client, auth_headers):
    response = client.get("/deals?status=unknown", headers=auth_headers)
    assert response.status_code == 422
