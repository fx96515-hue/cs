from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.data_quality_flag import DataQualityFlag
from app.models.user import User


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (list, tuple, set)) and len(value) == 0:
        return True
    return False


def _missing_field_flags(entity_type: str, instance: Any) -> list[dict[str, Any]]:
    data = instance.__dict__
    rules: dict[str, list[str]] = {
        "cooperative": ["region_id", "region", "contact_email", "website"],
        "roaster": ["city", "contact_email", "website", "price_position"],
        "lot": ["price_per_kg", "currency", "weight_kg", "expected_cupping_score", "processing", "varieties"],
        "shipment": [
            "container_number",
            "bill_of_lading",
            "origin_port",
            "destination_port",
            "departure_date",
            "estimated_arrival",
        ],
        "deal": ["status", "price_per_kg", "currency", "weight_kg"],
    }
    fields = rules.get(entity_type, [])
    flags: list[dict[str, Any]] = []
    for field_name in fields:
        value = data.get(field_name)
        if _is_missing(value):
            flags.append(
                {
                    "field_name": field_name,
                    "issue_type": "missing_field",
                    "severity": "warning",
                    "message": f"Missing {field_name}",
                }
            )
    return flags


def recompute_entity_flags(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    instance: Any,
    user: User | None = None,
    source_id: int | None = None,
) -> dict[str, int]:
    now = datetime.utcnow()
    existing = (
        db.query(DataQualityFlag)
        .filter(
            DataQualityFlag.entity_type == entity_type,
            DataQualityFlag.entity_id == entity_id,
            DataQualityFlag.resolved_at.is_(None),
        )
        .all()
    )
    for flag in existing:
        flag.resolved_at = now
        flag.resolved_by = user.email if user else "system"

    new_flags = _missing_field_flags(entity_type, instance)
    for flag in new_flags:
        db.add(
            DataQualityFlag(
                entity_type=entity_type,
                entity_id=entity_id,
                field_name=flag.get("field_name"),
                issue_type=flag.get("issue_type"),
                severity=flag.get("severity", "info"),
                message=flag.get("message"),
                confidence=flag.get("confidence"),
                detected_at=now,
                source_id=source_id,
            )
        )

    db.commit()
    return {"resolved": len(existing), "created": len(new_flags)}


def resolve_entity_flags(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    user: User | None = None,
) -> int:
    now = datetime.utcnow()
    existing = (
        db.query(DataQualityFlag)
        .filter(
            DataQualityFlag.entity_type == entity_type,
            DataQualityFlag.entity_id == entity_id,
            DataQualityFlag.resolved_at.is_(None),
        )
        .all()
    )
    for flag in existing:
        flag.resolved_at = now
        flag.resolved_by = user.email if user else "system"
    db.commit()
    return len(existing)
