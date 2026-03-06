from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, inspect as sa_inspect
from sqlalchemy.orm import Session

from app.models.entity_version import EntityVersion
from app.models.user import User


def serialize_model(instance: Any) -> dict[str, Any]:
    mapper = sa_inspect(instance).mapper
    return {attr.key: getattr(instance, attr.key) for attr in mapper.column_attrs}


def capture_entity_version(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    instance: Any,
    user: User | None = None,
    reason: str | None = None,
) -> None:
    payload = serialize_model(instance)
    last_version = (
        db.query(func.max(EntityVersion.version))
        .filter(
            EntityVersion.entity_type == entity_type,
            EntityVersion.entity_id == entity_id,
        )
        .scalar()
    )
    next_version = (last_version or 0) + 1
    record = EntityVersion(
        entity_type=entity_type,
        entity_id=entity_id,
        version=next_version,
        payload=payload,
        changed_by=user.email if user else None,
        change_reason=reason,
        created_at=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
