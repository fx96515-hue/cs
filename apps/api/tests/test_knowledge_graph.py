from __future__ import annotations

import pytest
from app.models.cooperative import Cooperative
from app.models.region import Region
from app.models.roaster import Roaster
from app.services import knowledge_graph


def test_build_empty_graph(db):
    """Test building graph with no data."""
    G = knowledge_graph.build_graph(db)
    assert G.number_of_nodes() == 0
    assert G.number_of_edges() == 0


def test_build_graph_with_cooperatives(db):
    """Test building graph with cooperatives."""
    coop1 = Cooperative(
        name="Coop A", region="Cajamarca", certifications="Organic, Fair Trade"
    )
    coop2 = Cooperative(name="Coop B", region="Cajamarca", certifications="Organic")
    db.add_all([coop1, coop2])
    db.commit()

    G = knowledge_graph.build_graph(db)

    # Should have 2 cooperatives + 1 region + 2 certifications = 5 nodes
    assert G.number_of_nodes() >= 5
    assert G.has_node("cooperative_1")
    assert G.has_node("cooperative_2")
    assert G.has_node("region_cajamarca")
    assert G.has_node("certification_organic")
    assert G.has_node("certification_fair_trade")


def test_graph_cooperative_region_edges(db):
    """Test that cooperatives are connected to their regions."""
    coop = Cooperative(name="Coop A", region="Cusco")
    region = Region(name="Cusco", country="Peru")
    db.add_all([coop, region])
    db.commit()

    G = knowledge_graph.build_graph(db)

    assert G.has_edge("cooperative_1", "region_cusco")
    edge_data = G.get_edge_data("cooperative_1", "region_cusco")
    assert edge_data["edge_type"] == "LOCATED_IN"


def test_graph_cooperative_certification_edges(db):
    """Test that cooperatives are connected to their certifications."""
    coop = Cooperative(name="Coop A", certifications="Organic, Fair Trade")
    db.add(coop)
    db.commit()

    G = knowledge_graph.build_graph(db)

    assert G.has_edge("cooperative_1", "certification_organic")
    assert G.has_edge("cooperative_1", "certification_fair_trade")

    edge_data = G.get_edge_data("cooperative_1", "certification_organic")
    assert edge_data["edge_type"] == "HAS_CERTIFICATION"


def test_graph_roaster_region_edges(db):
    """Test that roasters with Peru focus are connected to regions.

    Note: This test verifies the ASSUMPTION that Peru-focused roasters
    are connected to all regions with cooperatives. In production, this
    should be based on actual sourcing relationships.
    """
    roaster = Roaster(name="Roaster A", city="Berlin", peru_focus=True)
    region = Region(name="Cajamarca", country="Peru")
    coop = Cooperative(name="Coop A", region="Cajamarca")
    db.add_all([roaster, region, coop])
    db.commit()

    G = knowledge_graph.build_graph(db)

    assert G.has_edge("roaster_1", "region_cajamarca")
    edge_data = G.get_edge_data("roaster_1", "region_cajamarca")
    assert edge_data["edge_type"] == "SOURCES_FROM"


def test_graph_similar_cooperatives(db):
    """Test that similar cooperatives are connected."""
    coop1 = Cooperative(name="Coop A", region="Cusco", certifications="Organic")
    coop2 = Cooperative(
        name="Coop B", region="Cusco", certifications="Organic, Fair Trade"
    )
    db.add_all([coop1, coop2])
    db.commit()

    G = knowledge_graph.build_graph(db)

    # Cooperatives in same region with shared certification should be connected
    assert G.has_edge("cooperative_1", "cooperative_2")
    edge_data = G.get_edge_data("cooperative_1", "cooperative_2")
    assert edge_data["edge_type"] == "SIMILAR_PROFILE"


def test_graph_similar_roasters(db):
    """Test that similar roasters are connected."""
    roaster1 = Roaster(name="Roaster A", city="Berlin", price_position="premium")
    roaster2 = Roaster(name="Roaster B", city="Berlin", price_position="premium")
    db.add_all([roaster1, roaster2])
    db.commit()

    G = knowledge_graph.build_graph(db)

    # Roasters in same city with same price position should be connected
    assert G.has_edge("roaster_1", "roaster_2")
    edge_data = G.get_edge_data("roaster_1", "roaster_2")
    assert edge_data["edge_type"] == "SIMILAR_PROFILE"


def test_get_network_data(db):
    """Test getting network data for visualization."""
    coop = Cooperative(name="Coop A", region="Cusco", certifications="Organic")
    region = Region(name="Cusco", country="Peru")
    db.add_all([coop, region])
    db.commit()

    network_data = knowledge_graph.get_network_data(db)

    assert network_data.stats.total_nodes >= 3  # coop + region + cert
    assert network_data.stats.total_edges >= 2  # coop->region, coop->cert
    assert len(network_data.nodes) >= 3
    assert len(network_data.edges) >= 2
    assert "cooperative" in network_data.stats.node_types
    assert "region" in network_data.stats.node_types


def test_get_network_data_filtered(db):
    """Test getting network data with node type filter."""
    coop = Cooperative(name="Coop A", region="Cusco")
    roaster = Roaster(name="Roaster A", city="Berlin")
    db.add_all([coop, roaster])
    db.commit()

    network_data = knowledge_graph.get_network_data(db, node_types="cooperative,region")

    # Should only include cooperatives and regions
    for node in network_data.nodes:
        assert node.node_type in ["cooperative", "region"]


def test_get_entity_analysis(db):
    """Test getting entity analysis."""
    coop = Cooperative(name="Coop A", region="Cusco", certifications="Organic")
    region = Region(name="Cusco", country="Peru")
    db.add_all([coop, region])
    db.commit()

    analysis = knowledge_graph.get_entity_analysis(db, "cooperative", 1)

    assert analysis.entity_id == "cooperative_1"
    assert analysis.entity_name == "Coop A"
    assert analysis.entity_type == "cooperative"
    assert analysis.degree >= 2  # Connected to region and certification
    assert 0 <= analysis.degree_centrality <= 1
    assert 0 <= analysis.betweenness_centrality <= 1
    assert len(analysis.neighbors) >= 2


def test_get_entity_analysis_not_found(db):
    """Test getting analysis for non-existent entity."""
    with pytest.raises(ValueError, match="not found in graph"):
        knowledge_graph.get_entity_analysis(db, "cooperative", 999)


def test_get_communities(db):
    """Test community detection."""
    # Create two clusters of cooperatives
    coop1 = Cooperative(name="Coop A", region="Cusco", certifications="Organic")
    coop2 = Cooperative(name="Coop B", region="Cusco", certifications="Organic")
    coop3 = Cooperative(name="Coop C", region="Cajamarca", certifications="Fair Trade")
    db.add_all([coop1, coop2, coop3])
    db.commit()

    communities = knowledge_graph.get_communities(db)

    assert len(communities) > 0
    for community in communities:
        assert community.size > 0
        assert len(community.members) == community.size
        assert community.dominant_type in ["cooperative", "region", "certification"]


def test_get_shortest_path(db):
    """Test shortest path calculation."""
    coop = Cooperative(name="Coop A", region="Cusco", certifications="Organic")
    region = Region(name="Cusco", country="Peru")
    db.add_all([coop, region])
    db.commit()

    path_result = knowledge_graph.get_shortest_path(
        db, "cooperative", 1, "region", "cusco"
    )

    assert path_result.source.id == "cooperative_1"
    assert path_result.target.node_type == "region"
    assert path_result.total_hops >= 1
    assert len(path_result.path) == path_result.total_hops + 1
    assert len(path_result.edges) == path_result.total_hops


def test_get_shortest_path_no_path(db):
    """Test shortest path when no path exists."""
    coop1 = Cooperative(name="Coop A", region="Cusco")
    coop2 = Cooperative(name="Coop B")  # No region, isolated
    db.add_all([coop1, coop2])
    db.commit()

    with pytest.raises(ValueError, match="No path found"):
        knowledge_graph.get_shortest_path(db, "cooperative", 1, "cooperative", 2)


def test_get_hidden_connections(db):
    """Test finding hidden connections."""
    # Create a path: coop1 -> region -> coop2
    coop1 = Cooperative(name="Coop A", region="Cusco")
    coop2 = Cooperative(name="Coop B", region="Cusco")
    region = Region(name="Cusco", country="Peru")
    db.add_all([coop1, coop2, region])
    db.commit()

    hidden = knowledge_graph.get_hidden_connections(db, "cooperative", 1, max_hops=3)

    # Should find coop2 as a hidden connection (2 hops away via region)
    assert len(hidden) >= 1
    for connection in hidden:
        assert connection.hops >= 2
        assert connection.hops <= 3
        assert len(connection.connection_path) == connection.hops + 1


def test_cache_functionality(db):
    """Test that caching works correctly."""
    coop = Cooperative(name="Coop A", region="Cusco")
    db.add(coop)
    db.commit()

    # First call should build graph
    knowledge_graph.invalidate_cache()
    network_data1 = knowledge_graph.get_network_data(db)

    # Second call should use cache
    network_data2 = knowledge_graph.get_network_data(db)

    assert network_data1.stats.total_nodes == network_data2.stats.total_nodes

    # Invalidate and rebuild
    knowledge_graph.invalidate_cache()
    network_data3 = knowledge_graph.get_network_data(db)

    assert network_data3.stats.total_nodes == network_data1.stats.total_nodes


def test_graph_node_properties(db):
    """Test that node properties are correctly set."""
    coop = Cooperative(
        name="Coop A",
        region="Cusco",
        altitude_m=1800.0,
        total_score=8.5,
        certifications="Organic",
    )
    db.add(coop)
    db.commit()

    G = knowledge_graph.build_graph(db)

    node_data = G.nodes["cooperative_1"]
    assert node_data["label"] == "Coop A"
    assert node_data["node_type"] == "cooperative"
    assert node_data["properties"]["region"] == "Cusco"
    assert node_data["properties"]["altitude_m"] == 1800.0
    assert node_data["properties"]["total_score"] == 8.5


# API Integration Tests


def test_api_get_network(client, auth_headers, db):
    """Test GET /graph/network endpoint."""
    # Create test data
    coop = Cooperative(name="Coop A", region="Cusco", certifications="Organic")
    region = Region(name="Cusco", country="Peru")
    db.add_all([coop, region])
    db.commit()

    response = client.get("/graph/network", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert "stats" in data
    assert len(data["nodes"]) >= 3  # coop + region + cert
    assert data["stats"]["total_nodes"] >= 3


def test_api_get_network_filtered(client, auth_headers, db):
    """Test GET /graph/network with node type filter."""
    coop = Cooperative(name="Coop A", region="Cusco")
    roaster = Roaster(name="Roaster A", city="Berlin")
    db.add_all([coop, roaster])
    db.commit()

    response = client.get(
        "/graph/network?node_types=cooperative,region", headers=auth_headers
    )
    assert response.status_code == 200

    data = response.json()
    # Should only include cooperatives and regions
    for node in data["nodes"]:
        assert node["node_type"] in ["cooperative", "region"]


def test_api_get_entity_analysis(client, auth_headers, db):
    """Test GET /graph/analysis/{entity_type}/{entity_id} endpoint."""
    coop = Cooperative(name="Coop A", region="Cusco", certifications="Organic")
    region = Region(name="Cusco", country="Peru")
    db.add_all([coop, region])
    db.commit()

    response = client.get("/graph/analysis/cooperative/1", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["entity_id"] == "cooperative_1"
    assert data["entity_name"] == "Coop A"
    assert data["entity_type"] == "cooperative"
    assert data["degree"] >= 2
    assert "degree_centrality" in data
    assert "betweenness_centrality" in data
    assert "neighbors" in data


def test_api_get_entity_analysis_not_found(client, auth_headers, db):
    """Test GET /graph/analysis with non-existent entity."""
    response = client.get("/graph/analysis/cooperative/999", headers=auth_headers)
    assert response.status_code == 404


def test_api_get_communities(client, auth_headers, db):
    """Test GET /graph/communities endpoint."""
    # Create test data with multiple cooperatives
    coop1 = Cooperative(name="Coop A", region="Cusco", certifications="Organic")
    coop2 = Cooperative(name="Coop B", region="Cusco", certifications="Organic")
    db.add_all([coop1, coop2])
    db.commit()

    response = client.get("/graph/communities", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        community = data[0]
        assert "community_id" in community
        assert "size" in community
        assert "members" in community
        assert "dominant_type" in community


def test_api_get_communities_requires_analyst_role(client, test_viewer_user, db):
    """Test GET /graph/communities requires analyst role."""
    from app.core.security import create_access_token

    # Create viewer auth headers
    token = create_access_token(sub=test_viewer_user.email, role=test_viewer_user.role)
    viewer_headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/graph/communities", headers=viewer_headers)
    assert response.status_code == 403  # Forbidden


def test_api_get_shortest_path(client, auth_headers, db):
    """Test GET /graph/path/{source_type}/{source_id}/{target_type}/{target_id} endpoint."""
    coop = Cooperative(name="Coop A", region="Cusco", certifications="Organic")
    region = Region(name="Cusco", country="Peru")
    db.add_all([coop, region])
    db.commit()

    response = client.get(
        "/graph/path/cooperative/1/region/cusco", headers=auth_headers
    )
    assert response.status_code == 200

    data = response.json()
    assert "source" in data
    assert "target" in data
    assert "path" in data
    assert "edges" in data
    assert "total_hops" in data
    assert data["source"]["id"] == "cooperative_1"


def test_api_get_shortest_path_no_path(client, auth_headers, db):
    """Test GET /graph/path when no path exists."""
    coop1 = Cooperative(name="Coop A", region="Cusco")
    coop2 = Cooperative(name="Coop B")  # No region, isolated
    db.add_all([coop1, coop2])
    db.commit()

    response = client.get(
        "/graph/path/cooperative/1/cooperative/2", headers=auth_headers
    )
    assert response.status_code == 404


def test_api_get_hidden_connections(client, auth_headers, db):
    """Test GET /graph/hidden-connections/{entity_type}/{entity_id} endpoint."""
    # Create a path: coop1 -> region -> coop2
    coop1 = Cooperative(name="Coop A", region="Cusco")
    coop2 = Cooperative(name="Coop B", region="Cusco")
    region = Region(name="Cusco", country="Peru")
    db.add_all([coop1, coop2, region])
    db.commit()

    response = client.get(
        "/graph/hidden-connections/cooperative/1?max_hops=3", headers=auth_headers
    )
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    for connection in data:
        assert "entity" in connection
        assert "connection_path" in connection
        assert "hops" in connection
        assert "reason" in connection
        assert connection["hops"] >= 2


def test_api_get_hidden_connections_invalid_max_hops(client, auth_headers, db):
    """Test GET /graph/hidden-connections with invalid max_hops."""
    coop = Cooperative(name="Coop A", region="Cusco")
    db.add(coop)
    db.commit()

    # max_hops must be between 2 and 5
    response = client.get(
        "/graph/hidden-connections/cooperative/1?max_hops=1", headers=auth_headers
    )
    assert response.status_code == 422  # Validation error


def test_api_requires_authentication(client, db):
    """Test that all endpoints require authentication."""
    endpoints = [
        "/graph/network",
        "/graph/analysis/cooperative/1",
        "/graph/communities",
        "/graph/path/cooperative/1/region/cusco",
        "/graph/hidden-connections/cooperative/1",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden
