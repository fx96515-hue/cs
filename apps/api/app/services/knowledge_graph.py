from __future__ import annotations

import time

import networkx as nx
import structlog
from sqlalchemy.orm import Session

from app.models.cooperative import Cooperative
from app.models.region import Region
from app.models.roaster import Roaster
from app.schemas.knowledge_graph import (
    Community,
    EntityAnalysis,
    GraphEdge,
    GraphNode,
    GraphStats,
    HiddenConnection,
    NetworkData,
    PathResult,
)

logger = structlog.get_logger()

# In-memory cache for graph
_graph_cache: dict[str, tuple[nx.Graph, float]] = {}
CACHE_TTL = 300  # 5 minutes


def _get_or_build_graph(db: Session) -> nx.Graph:
    """Return cached graph or build new one."""
    cache_key = "main_graph"
    now = time.time()

    if cache_key in _graph_cache:
        cached_graph, timestamp = _graph_cache[cache_key]
        if now - timestamp < CACHE_TTL:
            logger.info("knowledge_graph.cache_hit")
            return cached_graph

    logger.info("knowledge_graph.building_graph")
    graph = build_graph(db)
    _graph_cache[cache_key] = (graph, now)
    return graph


def build_graph(db: Session) -> nx.Graph:
    """Build the knowledge graph from database entities."""
    G = nx.Graph()

    # Fetch all entities
    cooperatives = db.query(Cooperative).all()
    roasters = db.query(Roaster).all()
    regions = db.query(Region).all()

    # Add nodes for cooperatives
    for coop in cooperatives:
        node_id = f"cooperative_{coop.id}"
        G.add_node(
            node_id,
            label=coop.name,
            node_type="cooperative",
            properties={
                "id": coop.id,
                "region": coop.region,
                "altitude_m": coop.altitude_m,
                "certifications": coop.certifications,
                "varieties": coop.varieties,
                "total_score": coop.total_score,
            },
        )

    # Add nodes for roasters
    for roaster in roasters:
        node_id = f"roaster_{roaster.id}"
        G.add_node(
            node_id,
            label=roaster.name,
            node_type="roaster",
            properties={
                "id": roaster.id,
                "city": roaster.city,
                "peru_focus": roaster.peru_focus,
                "specialty_focus": roaster.specialty_focus,
                "price_position": roaster.price_position,
                "total_score": roaster.total_score,
            },
        )

    # Add nodes for regions
    for region in regions:
        node_id = f"region_{region.name.lower().replace(' ', '_')}"
        G.add_node(
            node_id,
            label=region.name,
            node_type="region",
            properties={
                "id": region.id,
                "country": region.country,
                "production_share_pct": region.production_share_pct,
                "quality_consistency_score": region.quality_consistency_score,
            },
        )

    # Also add region nodes from cooperative.region strings if not already present.
    # This ensures region nodes exist even when no Region model row was created.
    for coop in cooperatives:
        if coop.region:
            region_node_id = f"region_{coop.region.lower().replace(' ', '_')}"
            if not G.has_node(region_node_id):
                G.add_node(
                    region_node_id,
                    label=coop.region,
                    node_type="region",
                    properties={
                        "id": coop.region.lower(),
                        "country": None,
                        "production_share_pct": None,
                        "quality_consistency_score": None,
                    },
                )

    # Collect unique certifications
    certifications_set: set[str] = set()
    for coop in cooperatives:
        if coop.certifications:
            certs = [c.strip() for c in coop.certifications.split(",")]
            certifications_set.update(certs)

    # Add nodes for certifications
    for cert in certifications_set:
        if cert:
            node_id = f"certification_{cert.lower().replace(' ', '_')}"
            G.add_node(
                node_id,
                label=cert,
                node_type="certification",
                properties={"name": cert},
            )

    # Add edges: cooperative -> region (LOCATED_IN)
    for coop in cooperatives:
        if coop.region:
            coop_id = f"cooperative_{coop.id}"
            region_id = f"region_{coop.region.lower().replace(' ', '_')}"
            if G.has_node(region_id):
                G.add_edge(coop_id, region_id, edge_type="LOCATED_IN", weight=1.0)

    # Add edges: cooperative -> certification (HAS_CERTIFICATION)
    for coop in cooperatives:
        if coop.certifications:
            coop_id = f"cooperative_{coop.id}"
            certs = [c.strip() for c in coop.certifications.split(",")]
            for cert in certs:
                if cert:
                    cert_id = f"certification_{cert.lower().replace(' ', '_')}"
                    if G.has_node(cert_id):
                        G.add_edge(
                            coop_id, cert_id, edge_type="HAS_CERTIFICATION", weight=1.0
                        )

    # Add edges: roaster -> region (SOURCES_FROM)
    # NOTE: This creates a SOURCES_FROM edge from every Peru-focused roaster to every region
    # that has cooperatives. This is an ASSUMPTION that roasters with Peru focus might source
    # from any Peru region. In a production system, this should be based on actual sourcing
    # relationships tracked in the database.
    # Optimization: Collect unique regions first to avoid redundant iteration
    unique_region_ids = {
        f"region_{coop.region.lower().replace(' ', '_')}"
        for coop in cooperatives
        if coop.region
    }
    for roaster in roasters:
        if roaster.peru_focus:
            roaster_id = f"roaster_{roaster.id}"
            for region_id in unique_region_ids:
                if G.has_node(region_id):
                    G.add_edge(
                        roaster_id, region_id, edge_type="SOURCES_FROM", weight=1.0
                    )

    # Add edges: cooperative -> cooperative (SIMILAR_PROFILE)
    # Similar if they share region and at least one certification
    coop_list = list(cooperatives)
    for i, coop1 in enumerate(coop_list):
        for coop2 in coop_list[i + 1 :]:
            if coop1.region and coop2.region and coop1.region == coop2.region:
                # Check if they share certifications
                if coop1.certifications and coop2.certifications:
                    certs1 = set(c.strip() for c in coop1.certifications.split(","))
                    certs2 = set(c.strip() for c in coop2.certifications.split(","))
                    if certs1 & certs2:  # Intersection
                        coop1_id = f"cooperative_{coop1.id}"
                        coop2_id = f"cooperative_{coop2.id}"
                        G.add_edge(
                            coop1_id,
                            coop2_id,
                            edge_type="SIMILAR_PROFILE",
                            weight=0.7,
                        )

    # Add edges: roaster -> roaster (SIMILAR_PROFILE)
    # Similar if they have same city and price position
    roaster_list = list(roasters)
    for i, r1 in enumerate(roaster_list):
        for r2 in roaster_list[i + 1 :]:
            if (
                r1.city
                and r2.city
                and r1.city == r2.city
                and r1.price_position
                and r2.price_position
                and r1.price_position == r2.price_position
            ):
                r1_id = f"roaster_{r1.id}"
                r2_id = f"roaster_{r2.id}"
                G.add_edge(r1_id, r2_id, edge_type="SIMILAR_PROFILE", weight=0.7)

    # Add edges: roaster -> cooperative (TRADES_WITH)
    # A roaster trades with cooperatives located in regions it sources from.
    # Build a lookup: region_node_id -> list of cooperative node IDs
    region_to_coops: dict[str, list[str]] = {}
    for coop in cooperatives:
        if coop.region:
            region_node_id = f"region_{coop.region.lower().replace(' ', '_')}"
            region_to_coops.setdefault(region_node_id, []).append(
                f"cooperative_{coop.id}"
            )

    for roaster in roasters:
        if roaster.peru_focus:
            roaster_id = f"roaster_{roaster.id}"
            for region_id, coop_ids in region_to_coops.items():
                if G.has_node(region_id) and G.has_edge(roaster_id, region_id):
                    for coop_id in coop_ids:
                        if G.has_node(coop_id):
                            G.add_edge(
                                roaster_id,
                                coop_id,
                                edge_type="TRADES_WITH",
                                weight=0.8,
                            )

    logger.info(
        "knowledge_graph.graph_built",
        nodes=G.number_of_nodes(),
        edges=G.number_of_edges(),
    )

    return G


def get_network_data(db: Session, node_types: str = "all") -> NetworkData:
    """Get network data for visualization."""
    G = _get_or_build_graph(db)

    # Filter by node types if specified
    if node_types != "all":
        type_filter = set(t.strip() for t in node_types.split(","))
        nodes_to_keep = [
            n for n, data in G.nodes(data=True) if data["node_type"] in type_filter
        ]
        G = G.subgraph(nodes_to_keep).copy()

    # Build node list
    nodes = []
    for node_id, data in G.nodes(data=True):
        nodes.append(
            GraphNode(
                id=node_id,
                label=data["label"],
                node_type=data["node_type"],
                properties=data["properties"],
            )
        )

    # Build edge list
    edges = []
    for source, target, data in G.edges(data=True):
        edges.append(
            GraphEdge(
                source=source,
                target=target,
                edge_type=data["edge_type"],
                weight=data["weight"],
            )
        )

    # Calculate statistics
    node_type_counts: dict[str, int] = {}
    for node_id, data in G.nodes(data=True):
        node_type = data["node_type"]
        node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1

    density = nx.density(G) if G.number_of_nodes() > 0 else 0.0
    avg_degree = (
        sum(dict(G.degree()).values()) / G.number_of_nodes()
        if G.number_of_nodes() > 0
        else 0.0
    )

    stats = GraphStats(
        total_nodes=G.number_of_nodes(),
        total_edges=G.number_of_edges(),
        node_types=node_type_counts,
        density=density,
        avg_degree=avg_degree,
    )

    return NetworkData(nodes=nodes, edges=edges, stats=stats)


def get_entity_analysis(
    db: Session, entity_type: str, entity_id: int | str
) -> EntityAnalysis:
    """Get graph analysis for a specific entity."""
    G = _get_or_build_graph(db)

    # Handle different ID formats (numeric for most, string for regions/certifications)
    if isinstance(entity_id, int):
        node_id = f"{entity_type}_{entity_id}"
    else:
        node_id = f"{entity_type}_{str(entity_id).lower().replace(' ', '_')}"

    if not G.has_node(node_id):
        raise ValueError(f"Node {node_id} not found in graph")

    node_data = G.nodes[node_id]

    # Calculate centrality measures
    degree = G.degree(node_id)
    degree_centrality = nx.degree_centrality(G)[node_id]
    betweenness_centrality = nx.betweenness_centrality(G)[node_id]

    # Get neighbors
    neighbors = []
    for neighbor_id in G.neighbors(node_id):
        neighbor_data = G.nodes[neighbor_id]
        neighbors.append(
            GraphNode(
                id=neighbor_id,
                label=neighbor_data["label"],
                node_type=neighbor_data["node_type"],
                properties=neighbor_data["properties"],
            )
        )

    # Detect communities
    communities = list(nx.community.greedy_modularity_communities(G))
    community_id = None
    community_members = []

    for idx, community in enumerate(communities):
        if node_id in community:
            community_id = idx
            for member_id in community:
                member_data = G.nodes[member_id]
                community_members.append(
                    GraphNode(
                        id=member_id,
                        label=member_data["label"],
                        node_type=member_data["node_type"],
                        properties=member_data["properties"],
                    )
                )
            break

    return EntityAnalysis(
        entity_id=node_id,
        entity_name=node_data["label"],
        entity_type=entity_type,
        degree=degree,
        degree_centrality=degree_centrality,
        betweenness_centrality=betweenness_centrality,
        neighbors=neighbors,
        community_id=community_id,
        community_members=community_members,
    )


def get_communities(db: Session) -> list[Community]:
    """Detect communities in the knowledge graph."""
    G = _get_or_build_graph(db)

    communities = list(nx.community.greedy_modularity_communities(G))

    result = []
    for idx, community in enumerate(communities):
        members = []
        node_types: dict[str, int] = {}
        common_attrs: dict[str, int] = {}

        for node_id in community:
            node_data = G.nodes[node_id]
            members.append(
                GraphNode(
                    id=node_id,
                    label=node_data["label"],
                    node_type=node_data["node_type"],
                    properties=node_data["properties"],
                )
            )

            # Count node types
            node_type = node_data["node_type"]
            node_types[node_type] = node_types.get(node_type, 0) + 1

            # Collect common attributes (e.g., regions, certifications)
            if node_type == "region":
                common_attrs[node_data["label"]] = (
                    common_attrs.get(node_data["label"], 0) + 1
                )
            elif node_type == "certification":
                common_attrs[node_data["label"]] = (
                    common_attrs.get(node_data["label"], 0) + 1
                )

        # Determine dominant node type
        dominant_type = (
            max(node_types, key=lambda k: node_types[k]) if node_types else "unknown"
        )

        # Get most common attributes (sorted by frequency, descending)
        common_attributes = sorted(
            common_attrs.keys(), key=lambda k: common_attrs[k], reverse=True
        )[:5]

        result.append(
            Community(
                community_id=idx,
                size=len(community),
                members=members,
                dominant_type=dominant_type,
                common_attributes=common_attributes,
            )
        )

    return result


def get_shortest_path(
    db: Session,
    source_type: str,
    source_id: int | str,
    target_type: str,
    target_id: int | str,
) -> PathResult:
    """Find shortest path between two entities."""
    G = _get_or_build_graph(db)

    # Handle different ID formats (numeric for most, string for regions/certifications)
    if isinstance(source_id, int):
        source_node_id = f"{source_type}_{source_id}"
    else:
        source_node_id = f"{source_type}_{str(source_id).lower().replace(' ', '_')}"

    if isinstance(target_id, int):
        target_node_id = f"{target_type}_{target_id}"
    else:
        target_node_id = f"{target_type}_{str(target_id).lower().replace(' ', '_')}"

    if not G.has_node(source_node_id):
        raise ValueError(f"Source node {source_node_id} not found")
    if not G.has_node(target_node_id):
        raise ValueError(f"Target node {target_node_id} not found")

    try:
        path = nx.shortest_path(G, source_node_id, target_node_id)
    except nx.NetworkXNoPath:
        raise ValueError("No path found between source and target")

    # Build path nodes
    path_nodes = []
    for node_id in path:
        node_data = G.nodes[node_id]
        path_nodes.append(
            GraphNode(
                id=node_id,
                label=node_data["label"],
                node_type=node_data["node_type"],
                properties=node_data["properties"],
            )
        )

    # Build path edges
    path_edges = []
    for i in range(len(path) - 1):
        edge_data = G.get_edge_data(path[i], path[i + 1])
        path_edges.append(
            GraphEdge(
                source=path[i],
                target=path[i + 1],
                edge_type=edge_data["edge_type"],
                weight=edge_data["weight"],
            )
        )

    return PathResult(
        source=path_nodes[0],
        target=path_nodes[-1],
        path=path_nodes,
        edges=path_edges,
        total_hops=len(path) - 1,
    )


def get_hidden_connections(
    db: Session, entity_type: str, entity_id: int | str, max_hops: int = 3
) -> list[HiddenConnection]:
    """Find hidden connections to entities 2-3 hops away."""
    G = _get_or_build_graph(db)

    # Handle different ID formats (numeric for most, string for regions/certifications)
    if isinstance(entity_id, int):
        node_id = f"{entity_type}_{entity_id}"
    else:
        node_id = f"{entity_type}_{str(entity_id).lower().replace(' ', '_')}"

    if not G.has_node(node_id):
        raise ValueError(f"Node {node_id} not found in graph")

    # Use BFS to find nodes at distance 2 to max_hops
    direct_neighbors = set(G.neighbors(node_id))
    hidden = []

    # Get all nodes within max_hops
    path_lengths = nx.single_source_shortest_path_length(G, node_id, cutoff=max_hops)

    for target_node_id, distance in path_lengths.items():
        if (
            distance >= 2
            and distance <= max_hops
            and target_node_id not in direct_neighbors
        ):
            # Get the path
            path = nx.shortest_path(G, node_id, target_node_id)
            path_str = [G.nodes[n]["label"] for n in path]

            # Generate reason
            target_data = G.nodes[target_node_id]
            # Note: Using → for visual clarity. Ensure UTF-8 encoding in consuming systems.
            reason = f"Connected via {' → '.join(path_str[1:-1])}"

            hidden.append(
                HiddenConnection(
                    entity=GraphNode(
                        id=target_node_id,
                        label=target_data["label"],
                        node_type=target_data["node_type"],
                        properties=target_data["properties"],
                    ),
                    connection_path=path_str,
                    hops=distance,
                    reason=reason,
                )
            )

    return hidden


def invalidate_cache() -> None:
    """Invalidate the graph cache."""
    _graph_cache.clear()
    logger.info("knowledge_graph.cache_invalidated")
