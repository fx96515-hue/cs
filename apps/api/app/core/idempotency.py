from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


def find_existing_by_fields(
    db: Session, model: type[T], fields: dict[str, Any]
) -> T | None:
    if not fields:
        return None
    query = db.query(model)
    for key, value in fields.items():
        query = query.filter(getattr(model, key) == value)
    return query.first()
