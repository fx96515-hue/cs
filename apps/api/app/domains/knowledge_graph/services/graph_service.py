from __future__ import annotations

import time

import networkx as nx
import structlog
from sqlalchemy.orm import Session

from app.models.cooperative import Cooperative
from app.models.region import Region
from app.models.roaster import Roaster
from app.domains.knowledge_graph.schemas.knowledge_graph import (
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


def _region_node_id(region_name: str) -> str:
    return f"region_{region_name.lower().replace(' ', '_')}"


def _cert_node_id(cert_name: str) -> str:
    return f"certification_{cert_name.lower().replace(' ', '_')}"


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


def _add_cooperative_nodes(graph: nx.Graph, cooperatives: list[Cooperative]) -> None:
    for coop in cooperatives:
        graph.add_node(
            f"cooperative_{coop.id}",
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


def _add_roaster_nodes(graph: nx.Graph, roasters: list[Roaster]) -> None:
    for roaster in roasters:
        graph.add_node(
            f"roaster_{roaster.id}",
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


def _add_region_nodes(graph: nx.Graph, regions: list[Region]) -> None:
    for region in regions:
        graph.add_node(
            _region_node_id(region.name),
            label=region.name,
            node_type="region",
            properties={
                "id": region.id,
                "country": region.country,
                "production_share_pct": region.production_share_pct,
                "quality_consistency_score": region.quality_consistency_score,
            },
        )


def _ensure_region_nodes_from_coops(graph: nx.Graph, cooperatives: list[Cooperative]) -> None:
    for coop in cooperatives:
        if not coop.region:
            continue
        region_id = _region_node_id(coop.region)
        if graph.has_node(region_id):
            continue
        graph.add_node(
            region_id,
            label=coop.region,
            node_type="region",
            properties={
                "id": coop.region.lower(),
                "country": None,
                "production_share_pct": None,
                "quality_consistency_score": None,
            },
        )


def _collect_certifications(cooperatives: list[Cooperative]) -> set[str]:
    certifications: set[str] = set()
    for coop in cooperatives:
        if not coop.certifications:
            continue
        certifications.update(c.strip() for c in coop.certifications.split(",") if c.strip())
    return certifications


def _add_certification_nodes(graph: nx.Graph, certifications: set[str]) -> None:
    for cert in certifications:
        graph.add_node(
            _cert_node_id(cert),
            label=cert,
            node_type="certification",
            properties={"name": cert},
        )


def _add_coop_region_edges(graph: nx.Graph, cooperatives: list[Cooperative]) -> None:
    for coop in cooperatives:
        if not coop.region:
            continue
        coop_id = f"cooperative_{coop.id}"
        region_id = _region_node_id(coop.region)
        if graph.has_node(region_id):
            graph.add_edge(coop_id, region_id, edge_type="LOCATED_IN", weight=1.0)


def _add_coop_cert_edges(graph: nx.Graph, cooperatives: list[Cooperative]) -> None:
    for coop in cooperatives:
        if not coop.certifications:
            continue
        coop_id = f"cooperative_{coop.id}"
        for cert in (c.strip() for c in coop.certifications.split(",")):
            if not cert:
                continue
            cert_id = _cert_node_id(cert)
            if graph.has_node(cert_id):
                graph.add_edge(coop_id, cert_id, edge_type="HAS_CERTIFICATION", weight=1.0)


def _add_roaster_region_edges(graph: nx.Graph, roasters: list[Roaster], cooperatives: list[Cooperative]) -> None:
    unique_region_ids = {_region_node_id(coop.region) for coop in cooperatives if coop.region}
    for roaster in roasters:
        if not roaster.peru_focus:
            continue
        roaster_id = f"roaster_{roaster.id}"
        for region_id in unique_region_ids:
            if graph.has_node(region_id):
                graph.add_edge(roaster_id, region_id, edge_type="SOURCES_FROM", weight=1.0)


def _add_similar_coop_edges(graph: nx.Graph, cooperatives: list[Cooperative]) -> None:
    for i, coop1 in enumerate(cooperatives):
        for coop2 in cooperatives[i + 1 :]:
            if not coop1.region or coop1.region != coop2.region:
                continue
            if not coop1.certifications or not coop2.certifications:
                continue
            certs1 = set(c.strip() for c in coop1.certifications.split(","))
            certs2 = set(c.strip() for c in coop2.certifications.split(","))
            if certs1 & certs2:
                graph.add_edge(
                    f"cooperative_{coop1.id}",
                    f"cooperative_{coop2.id}",
                    edge_type="SIMILAR_PROFILE",
                    weight=0.7,
                )


def _add_similar_roaster_edges(graph: nx.Graph, roasters: list[Roaster]) -> None:
    for i, roaster1 in enumerate(roasters):
        for roaster2 in roasters[i + 1 :]:
            if not roaster1.city or roaster1.city != roaster2.city:
                continue
            if not roaster1.price_position or roaster1.price_position != roaster2.price_position:
                continue
            graph.add_edge(
                f"roaster_{roaster1.id}",
                f"roaster_{roaster2.id}",
                edge_type="SIMILAR_PROFILE",
                weight=0.7,
            )


def _build_region_to_coops(cooperatives: list[Cooperative]) -> dict[str, list[str]]:
    region_to_coops: dict[str, list[str]] = {}
    for coop in cooperatives:
        if not coop.region:
            continue
        region_to_coops.setdefault(_region_node_id(coop.region), []).append(f"cooperative_{coop.id}")
    return region_to_coops


def _roaster_trade_targets(
    graph: nx.Graph, roaster_id: str, region_to_coops: dict[str, list[str]]
) -> list[str]:
    targets: list[str] = []
    for region_id, coop_ids in region_to_coops.items():
        if not graph.has_node(region_id):
            continue
        if not graph.has_edge(roaster_id, region_id):
            continue
        targets.extend(coop_id for coop_id in coop_ids if graph.has_node(coop_id))
    return targets


def _add_roaster_trade_edges_for_targets(
    graph: nx.Graph, roaster_id: str, coop_ids: list[str]
) -> None:
    for coop_id in coop_ids:
        graph.add_edge(
            roaster_id,
            coop_id,
            edge_type="TRADES_WITH",
            weight=0.8,
        )


def _add_roaster_coop_trade_edges(graph: nx.Graph, roasters: list[Roaster], cooperatives: list[Cooperative]) -> None:
    region_to_coops = _build_region_to_coops(cooperatives)
    for roaster in roasters:
        if not roaster.peru_focus:
            continue
        roaster_id = f"roaster_{roaster.id}"
        targets = _roaster_trade_targets(graph, roaster_id, region_to_coops)
        _add_roaster_trade_edges_for_targets(graph, roaster_id, targets)


def build_graph(db: Session) -> nx.Graph:
    """Build the knowledge graph from database entities."""
    graph = nx.Graph()

    # Fetch all entities
    cooperatives = db.query(Cooperative).all()
    roasters = db.query(Roaster).all()
    regions = db.query(Region).all()

    _add_cooperative_nodes(graph, cooperatives)
    _add_roaster_nodes(graph, roasters)
    _add_region_nodes(graph, regions)
    _ensure_region_nodes_from_coops(graph, cooperatives)
    _add_certification_nodes(graph, _collect_certifications(cooperatives))
    _add_coop_region_edges(graph, cooperatives)
    _add_coop_cert_edges(graph, cooperatives)
    _add_roaster_region_edges(graph, roasters, cooperatives)
    _add_similar_coop_edges(graph, cooperatives)
    _add_similar_roaster_edges(graph, roasters)
    _add_roaster_coop_trade_edges(graph, roasters, cooperatives)

    logger.info(
        "knowledge_graph.graph_built",
        nodes=graph.number_of_nodes(),
        edges=graph.number_of_edges(),
    )

    return graph


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
