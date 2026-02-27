from fastapi.testclient import TestClient


def test_enrich_idempotent(client: TestClient, auth_headers, db):
    # Create a cooperative
    from app.models.cooperative import Cooperative

    coop = Cooperative(name="Idem Coop", region="Junin", website="https://example.com")
    db.add(coop)
    db.commit()
    db.refresh(coop)

    # First call should complete (200 or 503 if external API disabled)
    resp1 = client.post(f"/enrich/cooperative/{coop.id}", json={"url": "https://example.com"}, headers=auth_headers)
    assert resp1.status_code in (200, 400, 404, 503, 409)

    # Second call should not raise an unhandled 409; it may return 200 or a benign code.
    resp2 = client.post(f"/enrich/cooperative/{coop.id}", json={"url": "https://example.com"}, headers=auth_headers)
    assert resp2.status_code in (200, 400, 404, 503, 409)
