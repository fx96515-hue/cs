"""Tests for data quality API routes."""

from datetime import datetime, timezone

from app.models.cooperative import Cooperative
from app.models.data_quality_flag import DataQualityFlag


def _create_flag(
    db,
    *,
    entity_type: str = "cooperative",
    entity_id: int = 1,
    severity: str = "warning",
    resolved: bool = False,
) -> DataQualityFlag:
    now = datetime.now(timezone.utc)
    flag = DataQualityFlag(
        entity_type=entity_type,
        entity_id=entity_id,
        issue_type="missing_field",
        severity=severity,
        field_name="website",
        message="Missing website",
        detected_at=now,
        resolved_at=now if resolved else None,
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return flag


def test_list_data_quality_flags_filters(client, auth_headers, db):
    _create_flag(db, entity_id=11, severity="critical", resolved=False)
    _create_flag(db, entity_id=11, severity="warning", resolved=True)

    unresolved = client.get(
        "/data-quality/flags?entity_type=cooperative&entity_id=11&severity=critical",
        headers=auth_headers,
    )
    assert unresolved.status_code == 200
    payload = unresolved.json()
    assert len(payload) == 1
    assert payload[0]["severity"] == "critical"
    assert payload[0]["resolved_at"] is None

    include_resolved = client.get(
        "/data-quality/flags?entity_type=cooperative&entity_id=11&include_resolved=true",
        headers=auth_headers,
    )
    assert include_resolved.status_code == 200
    assert len(include_resolved.json()) == 2


def test_resolve_data_quality_flag(client, auth_headers, db):
    flag = _create_flag(db, entity_id=22, resolved=False)

    response = client.post(
        f"/data-quality/flags/{flag.id}/resolve",
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == flag.id
    assert payload["resolved_at"] is not None
    assert payload["resolved_by"] == "test@example.com"


def test_resolve_data_quality_flag_not_found(client, auth_headers):
    response = client.post("/data-quality/flags/99999/resolve", headers=auth_headers)
    assert response.status_code == 404


def test_recompute_flags_success(client, auth_headers, db, monkeypatch):
    cooperative = Cooperative(name="Coverage Coop")
    db.add(cooperative)
    db.commit()
    db.refresh(cooperative)

    def _fake_recompute(*, db, entity_type, entity_id, instance, user):
        assert entity_type == "cooperative"
        assert entity_id == cooperative.id
        assert instance.id == cooperative.id
        assert user.email == "test@example.com"
        return {"resolved": 1, "created": 2}

    monkeypatch.setattr(
        "app.api.routes.data_quality.recompute_entity_flags",
        _fake_recompute,
    )

    response = client.post(
        f"/data-quality/recompute/cooperative/{cooperative.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "resolved": 1, "created": 2}


def test_recompute_flags_invalid_entity_type(client, auth_headers):
    response = client.post("/data-quality/recompute/invalid/1", headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported entity_type"


def test_recompute_flags_entity_not_found(client, auth_headers):
    response = client.post(
        "/data-quality/recompute/cooperative/99999",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Not found"
