from __future__ import annotations

from pydantic import BaseModel


class GraphNode(BaseModel):
    """A node in the knowledge graph."""

    id: str  # e.g. "cooperative_42" or "region_cajamarca"
    label: str  # Display name
    node_type: str  # cooperative, roaster, region, certification
    properties: dict  # Additional data (score, altitude, etc.)


class GraphEdge(BaseModel):
    """An edge in the knowledge graph."""

    source: str  # Node ID
    target: str  # Node ID
    edge_type: (
        str  # LOCATED_IN, HAS_CERTIFICATION, SIMILAR_PROFILE, SOURCES_FROM, TRADES_WITH
    )
    weight: float = 1.0


class GraphStats(BaseModel):
    """Statistics about the knowledge graph."""

    total_nodes: int
    total_edges: int
    node_types: dict[str, int]  # {"cooperative": 50, "roaster": 30, ...}
    density: float
    avg_degree: float


class NetworkData(BaseModel):
    """Complete network data for visualization."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    stats: GraphStats


class EntityAnalysis(BaseModel):
    """Graph analysis for a specific entity."""

    entity_id: str
    entity_name: str
    entity_type: str
    degree: int
    degree_centrality: float
    betweenness_centrality: float
    neighbors: list[GraphNode]
    community_id: int | None
    community_members: list[GraphNode]


class Community(BaseModel):
    """A community detected in the knowledge graph."""

    community_id: int
    size: int
    members: list[GraphNode]
    dominant_type: str  # Which node type dominates
    common_attributes: list[str]  # Common certifications, regions, etc.


class PathResult(BaseModel):
    """Result of a shortest path query."""

    source: GraphNode
    target: GraphNode
    path: list[GraphNode]
    edges: list[GraphEdge]
    total_hops: int


class HiddenConnection(BaseModel):
    """A hidden connection between entities."""

    entity: GraphNode
    connection_path: list[str]  # Path as string list
    hops: int
    reason: str  # "Gleiche Zertifizierung via Region Cajamarca"
