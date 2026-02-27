from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.core.config import settings
from app.schemas.knowledge_graph import (
    Community,
    EntityAnalysis,
    HiddenConnection,
    NetworkData,
    PathResult,
)
from app.services import knowledge_graph

router = APIRouter()


def _require_graph_enabled() -> None:
    """Raise 503 when the graph feature flag is off."""
    if not getattr(settings, "GRAPH_ENABLED", False):
        raise HTTPException(
            status_code=503,
            detail="Knowledge graph is disabled (GRAPH_ENABLED=false).",
        )


def _parse_node_id(node_id: str) -> tuple[str, int | str]:
    """Parse a full node ID (e.g. 'cooperative_1', 'region_cajamarca') into (type, id).

    The id portion is returned as int when it is numeric, otherwise as str.
    Raises ValueError for malformed inputs.
    """
    parts = node_id.split("_", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid node_id format: {node_id}. Expected <type>_<id>.")
    entity_type, raw_id = parts
    try:
        return entity_type, int(raw_id)
    except ValueError:
        return entity_type, raw_id


@router.get("/network", response_model=NetworkData)
def get_network(
    node_types: str = Query(
        "all",
        description="Filter by node types: cooperative, roaster, region, certification",
    ),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
    __=Depends(_require_graph_enabled),
) -> NetworkData:
    """Get the complete knowledge graph network data for visualization."""
    return knowledge_graph.get_network_data(db, node_types=node_types)


@router.get("/analysis/{entity_type}/{entity_id}", response_model=EntityAnalysis)
def get_entity_analysis(
    entity_type: str,
    entity_id: str,  # Accept str to handle both numeric IDs and string-based IDs (regions, certs)
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
    __=Depends(_require_graph_enabled),
) -> EntityAnalysis:
    """Get graph analysis for a specific entity."""
    try:
        # Try to parse as int, otherwise keep as string
        parsed_id: int | str
        try:
            parsed_id = int(entity_id)
        except ValueError:
            parsed_id = entity_id
        return knowledge_graph.get_entity_analysis(db, entity_type, parsed_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/entity/{node_id}/connections", response_model=EntityAnalysis)
def get_entity_connections(
    node_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
    __=Depends(_require_graph_enabled),
) -> EntityAnalysis:
    """Get connections for a specific entity by full node ID (e.g. cooperative_1, roaster_2)."""
    try:
        entity_type, parsed_id = _parse_node_id(node_id)
        return knowledge_graph.get_entity_analysis(db, entity_type, parsed_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/communities", response_model=list[Community])
def get_communities(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
    __=Depends(_require_graph_enabled),
) -> list[Community]:
    """Detect and return communities in the knowledge graph."""
    return knowledge_graph.get_communities(db)


@router.get("/cluster", response_model=list[Community])
def get_clusters(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
    __=Depends(_require_graph_enabled),
) -> list[Community]:
    """Alias for /graph/communities – cluster detection in the knowledge graph."""
    return knowledge_graph.get_communities(db)


@router.get(
    "/path/{source_type}/{source_id}/{target_type}/{target_id}",
    response_model=PathResult,
)
def get_shortest_path(
    source_type: str,
    source_id: str,  # Accept str to handle both numeric IDs and string-based IDs
    target_type: str,
    target_id: str,  # Accept str to handle both numeric IDs and string-based IDs
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
    __=Depends(_require_graph_enabled),
) -> PathResult:
    """Find shortest path between two entities in the knowledge graph."""
    try:
        # Try to parse as int, otherwise keep as string
        parsed_source_id: int | str
        parsed_target_id: int | str
        try:
            parsed_source_id = int(source_id)
        except ValueError:
            parsed_source_id = source_id
        try:
            parsed_target_id = int(target_id)
        except ValueError:
            parsed_target_id = target_id

        return knowledge_graph.get_shortest_path(
            db, source_type, parsed_source_id, target_type, parsed_target_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/path/{from_id}/{to_id}", response_model=PathResult)
def get_path_by_node_ids(
    from_id: str,
    to_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
    __=Depends(_require_graph_enabled),
) -> PathResult:
    """Find shortest path between two entities using full node IDs (e.g. cooperative_1, roaster_2)."""
    try:
        source_type, parsed_source_id = _parse_node_id(from_id)
        target_type, parsed_target_id = _parse_node_id(to_id)
        return knowledge_graph.get_shortest_path(
            db, source_type, parsed_source_id, target_type, parsed_target_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/hidden-connections/{entity_type}/{entity_id}",
    response_model=list[HiddenConnection],
)
def get_hidden_connections(
    entity_type: str,
    entity_id: str,  # Accept str to handle both numeric IDs and string-based IDs
    max_hops: int = Query(3, ge=2, le=5, description="Maximum hops to search"),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
    __=Depends(_require_graph_enabled),
) -> list[HiddenConnection]:
    """Find hidden connections to entities 2-3 hops away."""
    try:
        # Try to parse as int, otherwise keep as string
        parsed_id: int | str
        try:
            parsed_id = int(entity_id)
        except ValueError:
            parsed_id = entity_id
        return knowledge_graph.get_hidden_connections(
            db, entity_type, parsed_id, max_hops
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
