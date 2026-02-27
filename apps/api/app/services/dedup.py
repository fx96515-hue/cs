from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast, Union
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

    items_list: list[Cooperative] | list[Roaster]
    if entity_type == "cooperative":
        items_list = db.query(Cooperative).all()
    else:
        items_list = db.query(Roaster).all()
    # group by domain when possible (strong signal)
    by_domain: dict[str, list[Any]] = {}
    no_domain: list[Any] = []
    for it in items_list:
        dom = _domain(getattr(it, "website", None))
        if dom:
            by_domain.setdefault(dom, []).append(it)
        else:
            no_domain.append(it)

    pairs: list[DedupPair] = []

    # Domain-based duplicates (same domain)
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

    # Name-based duplicates (simple blocking by first letter)
    buckets: dict[str, list[Any]] = {}
    for it in no_domain:
        k = (it.name or "").strip()[:1].lower() or "_"
        buckets.setdefault(k, []).append(it)

    for _, group in buckets.items():
        n = len(group)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = group[i], group[j]
                s = _score(a.name, b.name)
                if s >= threshold:
                    pairs.append(
                        DedupPair(a.id, b.id, a.name, b.name, s, "name_similarity")
                    )

    # sort + cut
    pairs.sort(key=lambda p: p.score, reverse=True)
    pairs = pairs[: max(0, min(limit_pairs, 500))]

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

    # Get entities with proper typing using Union to avoid type mismatch
    EntityType = Union[Cooperative, Roaster]

    if entity_type == "cooperative":
        keep_entity: EntityType = cast(Cooperative, db.get(Cooperative, keep_id))
        merge_entity: EntityType = cast(Cooperative, db.get(Cooperative, merge_id))
    else:
        keep_entity = cast(Roaster, db.get(Roaster, keep_id))
        merge_entity = cast(Roaster, db.get(Roaster, merge_id))

    if not keep_entity or not merge_entity:
        raise ValueError("One or both entities not found")

    if keep_id == merge_id:
        raise ValueError("Cannot merge entity with itself")

    # Store merge info
    merge_info = {
        "merged_from_id": merge_id,
        "merged_from_name": merge_entity.name,
        "merged_at": datetime.now().isoformat(),
    }

    # Create alias for merged entity name
    db.add(
        EntityAlias(
            entity_type=entity_type,
            entity_id=keep_id,
            alias=merge_entity.name,
            kind="name",
            observed_at=datetime.now(),
        )
    )

    # Merge fields: keep non-null values from merge_entity if keep_entity has null
    fields_to_merge = [
        "region",
        "altitude_m",
        "varieties",
        "certifications",
        "contact_email",
        "website",
        "notes",
    ]

    merged_fields = []
    for field in fields_to_merge:
        keep_val = getattr(keep_entity, field, None)
        merge_val = getattr(merge_entity, field, None)

        if merge_val and not keep_val:
            setattr(keep_entity, field, merge_val)
            merged_fields.append(field)

    # Merge scores: keep higher scores
    score_fields = [
        "quality_score",
        "reliability_score",
        "economics_score",
        "total_score",
    ]
    for field in score_fields:
        # Use getattr with default None to handle fields that don't exist
        keep_val = getattr(keep_entity, field, None) or 0
        merge_val = getattr(merge_entity, field, None) or 0
        if merge_val > keep_val and hasattr(keep_entity, field):
            setattr(keep_entity, field, merge_val)
            merged_fields.append(field)

    # Update meta with merge info
    keep_meta = keep_entity.meta or {}
    keep_meta["merge_history"] = keep_meta.get("merge_history", [])
    keep_meta["merge_history"].append(merge_info)
    keep_entity.meta = keep_meta

    # Deactivate merged entity
    merge_entity.status = "archived"
    merge_meta = merge_entity.meta or {}
    merge_meta["merged_into_id"] = keep_id
    merge_meta["merged_at"] = merge_info["merged_at"]
    merge_entity.meta = merge_meta

    # Create event records
    db.add(
        EntityEvent(
            entity_type=entity_type,
            entity_id=keep_id,
            event_type="entity_merged",
            payload={
                "action": "kept",
                "merged_from_id": merge_id,
                "merged_from_name": merge_entity.name,
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
                "merged_into_name": keep_entity.name,
            },
        )
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
