"""Unit tests for the knowledge graph service."""

from __future__ import annotations

from unittest.mock import MagicMock

import networkx as nx
import pytest

from app.services.knowledge_graph import (
    build_graph,
    get_entity_analysis,
    get_hidden_connections,
    get_network_data,
    get_shortest_path,
    invalidate_cache,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cooperative(
    id: int, name: str, region: str | None, certifications: str | None
):
    coop = MagicMock()
    coop.id = id
    coop.name = name
    coop.region = region
    coop.altitude_m = 1500
    coop.certifications = certifications
    coop.varieties = "Caturra"
    coop.total_score = 85.0
    return coop


def _make_roaster(
    id: int, name: str, city: str, peru_focus: bool, price_position: str | None = None
):
    roaster = MagicMock()
    roaster.id = id
    roaster.name = name
    roaster.city = city
    roaster.peru_focus = peru_focus
    roaster.specialty_focus = True
    roaster.price_position = price_position
    roaster.total_score = 80.0
    return roaster


def _make_region(id: int, name: str, country: str):
    region = MagicMock()
    region.id = id
    region.name = name
    region.country = country
    region.production_share_pct = 10.0
    region.quality_consistency_score = 0.9
    return region


def _make_db(cooperatives=None, roasters=None, regions=None):
    db = MagicMock()
    db.query.side_effect = lambda model: _make_query(
        model, cooperatives or [], roasters or [], regions or []
    )
    return db


def _make_query(model, cooperatives, roasters, regions):
    from app.models.cooperative import Cooperative
    from app.models.roaster import Roaster
    from app.models.region import Region

    q = MagicMock()
    if model is Cooperative:
        q.all.return_value = cooperatives
    elif model is Roaster:
        q.all.return_value = roasters
    elif model is Region:
        q.all.return_value = regions
    else:
        q.all.return_value = []
    return q


# ---------------------------------------------------------------------------
# build_graph
# ---------------------------------------------------------------------------


class TestBuildGraph:
    def test_empty_db_returns_empty_graph(self):
        db = _make_db()
        G = build_graph(db)
        assert isinstance(G, nx.Graph)
        assert G.number_of_nodes() == 0

    def test_cooperative_node_added(self):
        coops = [_make_cooperative(1, "Coop A", "Cajamarca", None)]
        db = _make_db(cooperatives=coops)
        G = build_graph(db)
        assert G.has_node("cooperative_1")
        assert G.nodes["cooperative_1"]["label"] == "Coop A"
        assert G.nodes["cooperative_1"]["node_type"] == "cooperative"

    def test_roaster_node_added(self):
        roasters = [_make_roaster(1, "Roaster X", "Hamburg", False)]
        db = _make_db(roasters=roasters)
        G = build_graph(db)
        assert G.has_node("roaster_1")
        assert G.nodes["roaster_1"]["node_type"] == "roaster"

    def test_region_node_added_from_region_model(self):
        regions = [_make_region(1, "Cajamarca", "Peru")]
        db = _make_db(regions=regions)
        G = build_graph(db)
        assert G.has_node("region_cajamarca")

    def test_region_node_added_from_cooperative_region_string(self):
        coops = [_make_cooperative(1, "Coop A", "San Martin", None)]
        db = _make_db(cooperatives=coops)
        G = build_graph(db)
        assert G.has_node("region_san_martin")

    def test_certification_node_added(self):
        coops = [_make_cooperative(1, "Coop A", None, "Organic, Fair Trade")]
        db = _make_db(cooperatives=coops)
        G = build_graph(db)
        assert G.has_node("certification_organic")
        assert G.has_node("certification_fair_trade")

    def test_located_in_edge(self):
        coops = [_make_cooperative(1, "Coop A", "Cajamarca", None)]
        db = _make_db(cooperatives=coops)
        G = build_graph(db)
        assert G.has_edge("cooperative_1", "region_cajamarca")
        assert G["cooperative_1"]["region_cajamarca"]["edge_type"] == "LOCATED_IN"

    def test_has_certification_edge(self):
        coops = [_make_cooperative(1, "Coop A", None, "Organic")]
        db = _make_db(cooperatives=coops)
        G = build_graph(db)
        assert G.has_edge("cooperative_1", "certification_organic")
        assert (
            G["cooperative_1"]["certification_organic"]["edge_type"]
            == "HAS_CERTIFICATION"
        )

    def test_sources_from_edge_for_peru_focused_roaster(self):
        coops = [_make_cooperative(1, "Coop A", "Cajamarca", None)]
        roasters = [_make_roaster(1, "Roaster X", "Hamburg", True)]
        db = _make_db(cooperatives=coops, roasters=roasters)
        G = build_graph(db)
        assert G.has_edge("roaster_1", "region_cajamarca")
        assert G["roaster_1"]["region_cajamarca"]["edge_type"] == "SOURCES_FROM"

    def test_no_sources_from_edge_for_non_peru_roaster(self):
        coops = [_make_cooperative(1, "Coop A", "Cajamarca", None)]
        roasters = [_make_roaster(1, "Roaster X", "Hamburg", False)]
        db = _make_db(cooperatives=coops, roasters=roasters)
        G = build_graph(db)
        assert not G.has_edge("roaster_1", "region_cajamarca")

    def test_trades_with_edge_peru_focused_roaster_and_cooperative(self):
        coops = [_make_cooperative(1, "Coop A", "Cajamarca", None)]
        roasters = [_make_roaster(1, "Roaster X", "Hamburg", True)]
        db = _make_db(cooperatives=coops, roasters=roasters)
        G = build_graph(db)
        assert G.has_edge("roaster_1", "cooperative_1")
        assert G["roaster_1"]["cooperative_1"]["edge_type"] == "TRADES_WITH"

    def test_no_trades_with_edge_for_non_peru_roaster(self):
        coops = [_make_cooperative(1, "Coop A", "Cajamarca", None)]
        roasters = [_make_roaster(1, "Roaster X", "Hamburg", False)]
        db = _make_db(cooperatives=coops, roasters=roasters)
        G = build_graph(db)
        assert not G.has_edge("roaster_1", "cooperative_1")

    def test_trades_with_edge_weight(self):
        coops = [_make_cooperative(1, "Coop A", "Cajamarca", None)]
        roasters = [_make_roaster(1, "Roaster X", "Hamburg", True)]
        db = _make_db(cooperatives=coops, roasters=roasters)
        G = build_graph(db)
        assert G["roaster_1"]["cooperative_1"]["weight"] == 0.8

    def test_trades_with_edges_multiple_cooperatives_same_region(self):
        coops = [
            _make_cooperative(1, "Coop A", "Cajamarca", None),
            _make_cooperative(2, "Coop B", "Cajamarca", None),
        ]
        roasters = [_make_roaster(1, "Roaster X", "Hamburg", True)]
        db = _make_db(cooperatives=coops, roasters=roasters)
        G = build_graph(db)
        assert G.has_edge("roaster_1", "cooperative_1")
        assert G.has_edge("roaster_1", "cooperative_2")
        assert G["roaster_1"]["cooperative_1"]["edge_type"] == "TRADES_WITH"
        assert G["roaster_1"]["cooperative_2"]["edge_type"] == "TRADES_WITH"

    def test_trades_with_edges_cooperatives_different_regions(self):
        coops = [
            _make_cooperative(1, "Coop A", "Cajamarca", None),
            _make_cooperative(2, "Coop B", "Cusco", None),
        ]
        roasters = [_make_roaster(1, "Roaster X", "Hamburg", True)]
        db = _make_db(cooperatives=coops, roasters=roasters)
        G = build_graph(db)
        assert G.has_edge("roaster_1", "cooperative_1")
        assert G.has_edge("roaster_1", "cooperative_2")
        assert G["roaster_1"]["cooperative_1"]["edge_type"] == "TRADES_WITH"
        assert G["roaster_1"]["cooperative_2"]["edge_type"] == "TRADES_WITH"

    def test_similar_profile_coop_edge(self):
        coops = [
            _make_cooperative(1, "Coop A", "Cajamarca", "Organic"),
            _make_cooperative(2, "Coop B", "Cajamarca", "Organic"),
        ]
        db = _make_db(cooperatives=coops)
        G = build_graph(db)
        assert G.has_edge("cooperative_1", "cooperative_2")
        assert G["cooperative_1"]["cooperative_2"]["edge_type"] == "SIMILAR_PROFILE"


# ---------------------------------------------------------------------------
# get_network_data
# ---------------------------------------------------------------------------


class TestGetNetworkData:
    def setup_method(self):
        invalidate_cache()

    def test_returns_network_data(self):
        coops = [_make_cooperative(1, "Coop A", "Cajamarca", "Organic")]
        roasters = [_make_roaster(1, "Roaster X", "Hamburg", True)]
        db = _make_db(cooperatives=coops, roasters=roasters)
        result = get_network_data(db)
        assert len(result.nodes) > 0
        assert result.stats.total_nodes > 0

    def test_filter_by_node_type(self):
        coops = [_make_cooperative(1, "Coop A", "Cajamarca", None)]
        roasters = [_make_roaster(1, "Roaster X", "Hamburg", True)]
        db = _make_db(cooperatives=coops, roasters=roasters)
        result = get_network_data(db, node_types="cooperative")
        for node in result.nodes:
            assert node.node_type == "cooperative"


# ---------------------------------------------------------------------------
# get_entity_analysis
# ---------------------------------------------------------------------------


class TestGetEntityAnalysis:
    def setup_method(self):
        invalidate_cache()

    def test_returns_analysis_for_cooperative(self):
        coops = [_make_cooperative(1, "Coop A", "Cajamarca", "Organic")]
        db = _make_db(cooperatives=coops)
        result = get_entity_analysis(db, "cooperative", 1)
        assert result.entity_id == "cooperative_1"
        assert result.entity_name == "Coop A"
        assert result.entity_type == "cooperative"

    def test_raises_for_unknown_entity(self):
        db = _make_db()
        with pytest.raises(ValueError, match="not found"):
            get_entity_analysis(db, "cooperative", 999)


# ---------------------------------------------------------------------------
# get_shortest_path
# ---------------------------------------------------------------------------


class TestGetShortestPath:
    def setup_method(self):
        invalidate_cache()

    def test_path_between_roaster_and_cooperative(self):
        coops = [_make_cooperative(1, "Coop A", "Cajamarca", None)]
        roasters = [_make_roaster(1, "Roaster X", "Hamburg", True)]
        db = _make_db(cooperatives=coops, roasters=roasters)
        # roaster_1 -> cooperative_1 via TRADES_WITH (direct edge)
        result = get_shortest_path(db, "roaster", 1, "cooperative", 1)
        assert result.source.id == "roaster_1"
        assert result.target.id == "cooperative_1"
        assert result.total_hops == 1

    def test_raises_when_source_missing(self):
        db = _make_db()
        with pytest.raises(ValueError, match="not found"):
            get_shortest_path(db, "cooperative", 999, "cooperative", 1)

    def test_raises_when_no_path(self):
        # Two isolated cooperatives in different regions, no common nodes
        coops = [
            _make_cooperative(1, "Coop A", "Cajamarca", None),
            _make_cooperative(2, "Coop B", "Cusco", None),
        ]
        db = _make_db(cooperatives=coops)
        with pytest.raises(ValueError, match="No path"):
            get_shortest_path(db, "cooperative", 1, "cooperative", 2)


# ---------------------------------------------------------------------------
# get_hidden_connections
# ---------------------------------------------------------------------------


class TestGetHiddenConnections:
    def setup_method(self):
        invalidate_cache()

    def test_returns_list(self):
        coops = [
            _make_cooperative(1, "Coop A", "Cajamarca", "Organic"),
            _make_cooperative(2, "Coop B", "Cajamarca", "Organic"),
        ]
        roasters = [_make_roaster(1, "Roaster X", "Hamburg", True)]
        db = _make_db(cooperatives=coops, roasters=roasters)
        result = get_hidden_connections(db, "cooperative", 1)
        assert isinstance(result, list)

    def test_raises_for_unknown_entity(self):
        db = _make_db()
        with pytest.raises(ValueError, match="not found"):
            get_hidden_connections(db, "cooperative", 999)


# ---------------------------------------------------------------------------
# invalidate_cache
# ---------------------------------------------------------------------------


class TestInvalidateCache:
    def test_cache_invalidated(self):
        coops = [_make_cooperative(1, "Coop A", "Cajamarca", None)]
        db = _make_db(cooperatives=coops)
        # Build graph once (populates cache)
        get_network_data(db)
        # Invalidate and rebuild – should not raise
        invalidate_cache()
        result = get_network_data(db)
        assert result.stats.total_nodes > 0
