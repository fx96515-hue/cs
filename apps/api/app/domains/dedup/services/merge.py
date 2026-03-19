from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from app.models.cooperative import Cooperative
from app.models.roaster import Roaster
from app.models.entity_alias import EntityAlias
from app.models.entity_event import EntityEvent


def _domain(url: str | None) -> str | None:
    if not url:
        return None
    try:
        return (urlparse(url).netloc or "").lower() or None
    except Exception:
        return None


@dataclass
class DedupPair:
    a_id: int
    b_id: int
    a_name: str
    b_name: str
    score: float
    reason: str


def _score(a_name: str | None, b_name: str | None) -> float:
    # token-based fuzzy score (0..100)
    return float(
        max(
            fuzz.token_set_ratio(a_name or "", b_name or ""),
            fuzz.token_sort_ratio(a_name or "", b_name or ""),
        )
    )


def _load_entities(db: Session, entity_type: str) -> list[Cooperative] | list[Roaster]:
    if entity_type == "cooperative":
        return db.query(Cooperative).all()
    return db.query(Roaster).all()


def _group_by_domain(
    items: list[Cooperative] | list[Roaster],
) -> tuple[dict[str, list[Any]], list[Any]]:
    by_domain: dict[str, list[Any]] = {}
    no_domain: list[Any] = []
    for item in items:
        dom = _domain(getattr(item, "website", None))
        if dom:
            by_domain.setdefault(dom, []).append(item)
        else:
            no_domain.append(item)
    return by_domain, no_domain


def _domain_pairs(by_domain: dict[str, list[Any]]) -> list[DedupPair]:
    pairs: list[DedupPair] = []
    for dom, group in by_domain.items():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                s = _score(a.name, b.name)
                pairs.append(
                    DedupPair(
                        a.id, b.id, a.name, b.name, max(s, 98.0), f"same_domain:{dom}"
                    )
                )
    return pairs


def _name_pairs(no_domain: list[Any], threshold: float) -> list[DedupPair]:
    pairs: list[DedupPair] = []
    buckets: dict[str, list[Any]] = {}
    for item in no_domain:
        key = (item.name or "").strip()[:1].lower() or "_"
        buckets.setdefault(key, []).append(item)

    for group in buckets.values():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                s = _score(a.name, b.name)
                if s >= threshold:
                    pairs.append(
                        DedupPair(a.id, b.id, a.name, b.name, s, "name_similarity")
                    )
    return pairs


def _limit_pairs(pairs: list[DedupPair], limit_pairs: int) -> list[DedupPair]:
    pairs.sort(key=lambda p: p.score, reverse=True)
    return pairs[: max(0, min(limit_pairs, 500))]


def _serialize_pairs(pairs: list[DedupPair]) -> list[dict[str, Any]]:
    return [
        {
            "a_id": p.a_id,
            "b_id": p.b_id,
            "a_name": p.a_name,
            "b_name": p.b_name,
            "score": p.score,
            "reason": p.reason,
        }
        for p in pairs
    ]


def suggest_duplicates(
    db: Session,
    *,
    entity_type: str,
    threshold: float = 90.0,
    limit_pairs: int = 50,
) -> list[dict[str, Any]]:
    """Suggest possible duplicates.

    This is intentionally conservative and optimized for small/medium datasets.
    """
    if entity_type not in {"cooperative", "roaster"}:
        raise ValueError("entity_type must be cooperative|roaster")

    items = _load_entities(db, entity_type)
    by_domain, no_domain = _group_by_domain(items)
    pairs = _domain_pairs(by_domain) + _name_pairs(no_domain, threshold)
    return _serialize_pairs(_limit_pairs(pairs, limit_pairs))


def _load_merge_pair(
    db: Session, *, entity_type: str, keep_id: int, merge_id: int
) -> tuple[Cooperative | Roaster, Cooperative | Roaster]:
    keep_entity: Cooperative | Roaster | None
    merge_entity: Cooperative | Roaster | None
    if entity_type == "cooperative":
        keep_entity = db.get(Cooperative, keep_id)
        merge_entity = db.get(Cooperative, merge_id)
    else:
        keep_entity = db.get(Roaster, keep_id)
        merge_entity = db.get(Roaster, merge_id)
    if not keep_entity or not merge_entity:
        raise ValueError("One or both entities not found")
    return keep_entity, merge_entity


def _create_merge_info(merge_id: int, merge_name: str) -> dict[str, Any]:
    return {
        "merged_from_id": merge_id,
        "merged_from_name": merge_name,
        "merged_at": datetime.now().isoformat(),
    }


def _create_name_alias(
    db: Session, *, entity_type: str, keep_id: int, merge_name: str
) -> None:
    db.add(
        EntityAlias(
            entity_type=entity_type,
            entity_id=keep_id,
            alias=merge_name,
            kind="name",
            observed_at=datetime.now(),
        )
    )


def _merge_nullable_fields(
    keep_entity: Cooperative | Roaster, merge_entity: Cooperative | Roaster
) -> list[str]:
    fields_to_merge = [
        "region",
        "altitude_m",
        "varieties",
        "certifications",
        "contact_email",
        "website",
        "notes",
    ]
    merged_fields: list[str] = []
    for field in fields_to_merge:
        keep_val = getattr(keep_entity, field, None)
        merge_val = getattr(merge_entity, field, None)
        if merge_val and not keep_val:
            setattr(keep_entity, field, merge_val)
            merged_fields.append(field)
    return merged_fields


def _merge_score_fields(
    keep_entity: Cooperative | Roaster, merge_entity: Cooperative | Roaster
) -> list[str]:
    score_fields = [
        "quality_score",
        "reliability_score",
        "economics_score",
        "total_score",
    ]
    merged_fields: list[str] = []
    for field in score_fields:
        keep_val = getattr(keep_entity, field, None) or 0
        merge_val = getattr(merge_entity, field, None) or 0
        if merge_val > keep_val and hasattr(keep_entity, field):
            setattr(keep_entity, field, merge_val)
            merged_fields.append(field)
    return merged_fields


def _append_merge_meta(
    entity: Cooperative | Roaster, merge_info: dict[str, Any]
) -> None:
    keep_meta = entity.meta or {}
    keep_meta["merge_history"] = keep_meta.get("merge_history", [])
    keep_meta["merge_history"].append(merge_info)
    entity.meta = keep_meta


def _archive_merged_entity(
    entity: Cooperative | Roaster, keep_id: int, merged_at: str
) -> None:
    entity.status = "archived"
    merge_meta = entity.meta or {}
    merge_meta["merged_into_id"] = keep_id
    merge_meta["merged_at"] = merged_at
    entity.meta = merge_meta


def _record_merge_events(
    db: Session,
    *,
    entity_type: str,
    keep_id: int,
    merge_id: int,
    keep_name: str,
    merge_name: str,
    merged_fields: list[str],
) -> None:
    db.add(
        EntityEvent(
            entity_type=entity_type,
            entity_id=keep_id,
            event_type="entity_merged",
            payload={
                "action": "kept",
                "merged_from_id": merge_id,
                "merged_from_name": merge_name,
                "merged_fields": merged_fields,
            },
        )
    )
    db.add(
        EntityEvent(
            entity_type=entity_type,
            entity_id=merge_id,
            event_type="entity_merged",
            payload={
                "action": "merged_into",
                "merged_into_id": keep_id,
                "merged_into_name": keep_name,
            },
        )
    )


def merge_entities(
    db: Session,
    *,
    entity_type: str,
    keep_id: int,
    merge_id: int,
) -> dict[str, Any]:
    """Merge two entities, keeping the best data.

    Args:
        db: Database session
        entity_type: 'cooperative' or 'roaster'
        keep_id: ID of entity to keep
        merge_id: ID of entity to merge (will be deactivated)

    Returns:
        Merge result dict
    """
    if entity_type not in {"cooperative", "roaster"}:
        raise ValueError("entity_type must be cooperative|roaster")

    if keep_id == merge_id:
        raise ValueError("Cannot merge entity with itself")
    keep_entity, merge_entity = _load_merge_pair(
        db, entity_type=entity_type, keep_id=keep_id, merge_id=merge_id
    )

    merge_info = _create_merge_info(merge_id, merge_entity.name)
    _create_name_alias(
        db, entity_type=entity_type, keep_id=keep_id, merge_name=merge_entity.name
    )
    merged_fields = _merge_nullable_fields(keep_entity, merge_entity)
    merged_fields.extend(_merge_score_fields(keep_entity, merge_entity))
    _append_merge_meta(keep_entity, merge_info)
    _archive_merged_entity(merge_entity, keep_id, merge_info["merged_at"])
    _record_merge_events(
        db,
        entity_type=entity_type,
        keep_id=keep_id,
        merge_id=merge_id,
        keep_name=keep_entity.name,
        merge_name=merge_entity.name,
        merged_fields=merged_fields,
    )

    db.commit()
    db.refresh(keep_entity)

    return {
        "status": "ok",
        "entity_type": entity_type,
        "keep_id": keep_id,
        "merge_id": merge_id,
        "merged_fields": merged_fields,
        "alias_created": merge_entity.name,
    }


def get_merge_history(
    db: Session, *, entity_type: str, limit: int = 50
) -> list[dict[str, Any]]:
    """Get merge history.

    Args:
        db: Database session
        entity_type: 'cooperative' or 'roaster'
        limit: Max results

    Returns:
        List of merge events
    """
    events = (
        db.query(EntityEvent)
        .filter(
            EntityEvent.entity_type == entity_type,
            EntityEvent.event_type == "entity_merged",
        )
        .order_by(EntityEvent.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "entity_id": e.entity_id,
            "created_at": e.created_at.isoformat()
            if hasattr(e.created_at, "isoformat")
            else str(e.created_at),
            "payload": e.payload,
        }
        for e in events
    ]
