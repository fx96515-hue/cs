from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.core.config import settings
from app.domains.knowledge_graph.schemas.knowledge_graph import (
    Community,
    EntityAnalysis,
    HiddenConnection,
    NetworkData,
    PathResult,
)
from app.domains.knowledge_graph.services import graph_service

router = APIRouter()
GraphEntityType = Literal["cooperative", "roaster", "region", "certification"]

NOT_FOUND_RESPONSES: dict[int | str, dict[str, Any]] = {
    404: {"description": "Entity not found"}
}
GRAPH_DISABLED_RESPONSES: dict[int | str, dict[str, Any]] = {
    503: {"description": "Knowledge graph is disabled"}
}
GRAPH_COMMON_RESPONSES: dict[int | str, dict[str, Any]] = {
    **NOT_FOUND_RESPONSES,
    **GRAPH_DISABLED_RESPONSES,
}
NOT_FOUND_DETAIL = "Not found"


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


@router.get("/network", responses=GRAPH_DISABLED_RESPONSES)
def get_network(
    node_types: Annotated[
        str,
        Query(
            description="Filter by node types: cooperative, roaster, region, certification",
        ),
    ] = "all",
    *,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
    __: Annotated[None, Depends(_require_graph_enabled)],
) -> NetworkData:
    """Get the complete knowledge graph network data for visualization."""
    return graph_service.get_network_data(db, node_types=node_types)


@router.get("/analysis/{entity_type}/{entity_id}", responses=GRAPH_COMMON_RESPONSES)
def get_entity_analysis(
    entity_type: GraphEntityType,
    entity_id: str,  # Accept str to handle both numeric IDs and string-based IDs (regions, certs)
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
    __: Annotated[None, Depends(_require_graph_enabled)],
) -> EntityAnalysis:
    """Get graph analysis for a specific entity."""
    try:
        # Try to parse as int, otherwise keep as string
        parsed_id: int | str
        try:
            parsed_id = int(entity_id)
        except ValueError:
            parsed_id = entity_id
        return graph_service.get_entity_analysis(db, entity_type, parsed_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)


@router.get("/entity/{node_id}/connections", responses=GRAPH_COMMON_RESPONSES)
def get_entity_connections(
    node_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
    __: Annotated[None, Depends(_require_graph_enabled)],
) -> EntityAnalysis:
    """Get connections for a specific entity by full node ID (e.g. cooperative_1, roaster_2)."""
    try:
        entity_type, parsed_id = _parse_node_id(node_id)
        return graph_service.get_entity_analysis(db, entity_type, parsed_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)


@router.get("/communities", responses=GRAPH_DISABLED_RESPONSES)
def get_communities(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
    __: Annotated[None, Depends(_require_graph_enabled)],
) -> list[Community]:
    """Detect and return communities in the knowledge graph."""
    return graph_service.get_communities(db)


@router.get("/cluster", responses=GRAPH_DISABLED_RESPONSES)
def get_clusters(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
    __: Annotated[None, Depends(_require_graph_enabled)],
) -> list[Community]:
    """Alias for /graph/communities - cluster detection in the knowledge graph."""
    return graph_service.get_communities(db)


@router.get(
    "/path/{source_type}/{source_id}/{target_type}/{target_id}",
    responses=GRAPH_COMMON_RESPONSES,
)
def get_shortest_path(
    source_type: GraphEntityType,
    source_id: str,  # Accept str to handle both numeric IDs and string-based IDs
    target_type: GraphEntityType,
    target_id: str,  # Accept str to handle both numeric IDs and string-based IDs
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
    __: Annotated[None, Depends(_require_graph_enabled)],
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

        return graph_service.get_shortest_path(
            db, source_type, parsed_source_id, target_type, parsed_target_id
        )
    except ValueError:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)


@router.get("/path/{from_id}/{to_id}", responses=GRAPH_COMMON_RESPONSES)
def get_path_by_node_ids(
    from_id: str,
    to_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
    __: Annotated[None, Depends(_require_graph_enabled)],
) -> PathResult:
    """Find shortest path between two entities using full node IDs (e.g. cooperative_1, roaster_2)."""
    try:
        source_type, parsed_source_id = _parse_node_id(from_id)
        target_type, parsed_target_id = _parse_node_id(to_id)
        return graph_service.get_shortest_path(
            db, source_type, parsed_source_id, target_type, parsed_target_id
        )
    except ValueError:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)


@router.get(
    "/hidden-connections/{entity_type}/{entity_id}",
    responses=GRAPH_COMMON_RESPONSES,
)
def get_hidden_connections(
    entity_type: GraphEntityType,
    entity_id: str,  # Accept str to handle both numeric IDs and string-based IDs
    max_hops: Annotated[
        int, Query(ge=2, le=5, description="Maximum hops to search")
    ] = 3,
    *,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
    __: Annotated[None, Depends(_require_graph_enabled)],
) -> list[HiddenConnection]:
    """Find hidden connections to entities 2-3 hops away."""
    try:
        # Try to parse as int, otherwise keep as string
        parsed_id: int | str
        try:
            parsed_id = int(entity_id)
        except ValueError:
            parsed_id = entity_id
        return graph_service.get_hidden_connections(
            db, entity_type, parsed_id, max_hops
        )
    except ValueError:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
