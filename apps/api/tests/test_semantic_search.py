"""Tests for semantic search API endpoints."""

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.cooperative import Cooperative
from app.models.roaster import Roaster


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_embedding(dims: int = 384) -> list[float]:
    """Return a list of *dims* floats (cheap mock vector)."""
    return [0.1] * dims


@contextmanager
def _search_enabled(enabled: bool = True):
    """Context manager: patch SEMANTIC_SEARCH_ENABLED on the route module."""
    with patch("app.api.routes.semantic_search.settings") as mock_settings:
        mock_settings.SEMANTIC_SEARCH_ENABLED = enabled
        yield mock_settings


# ---------------------------------------------------------------------------
# Feature-flag tests
# ---------------------------------------------------------------------------


class TestFeatureFlag:
    """When SEMANTIC_SEARCH_ENABLED=False, endpoints must return 503."""

    def test_semantic_search_disabled(self, client, auth_headers):
        with _search_enabled(False):
            response = client.get(
                "/search/semantic?q=test",
                headers=auth_headers,
            )
        assert response.status_code == 503
        assert "disabled" in response.json()["detail"].lower()

    def test_similar_entities_disabled(self, client, auth_headers, db):
        coop = Cooperative(name="Coop A", embedding=_make_embedding())
        db.add(coop)
        db.commit()
        db.refresh(coop)

        with _search_enabled(False):
            response = client.get(
                f"/search/entity/cooperative/{coop.id}/similar",
                headers=auth_headers,
            )
        assert response.status_code == 503


# ---------------------------------------------------------------------------
# /search/semantic tests
# ---------------------------------------------------------------------------


class TestSemanticSearch:
    """Tests for GET /search/semantic."""

    def _mock_service(self, embedding=None):
        """Return a mock EmbeddingService."""
        svc = MagicMock()
        svc.is_available.return_value = True
        svc.generate_embedding = AsyncMock(return_value=embedding or _make_embedding())
        return svc

    def test_missing_query_returns_422(self, client, auth_headers):
        response = client.get("/search/semantic", headers=auth_headers)
        assert response.status_code == 422

    def test_empty_query_returns_422(self, client, auth_headers):
        response = client.get("/search/semantic?q=", headers=auth_headers)
        assert response.status_code == 422

    def test_service_unavailable_returns_503(self, client, auth_headers):
        with (
            patch("app.api.routes.semantic_search.EmbeddingService") as mock_cls,
            _search_enabled(),
        ):
            svc = MagicMock()
            svc.is_available.return_value = False
            svc.provider_name = "local"
            mock_cls.return_value = svc
            response = client.get("/search/semantic?q=coffee", headers=auth_headers)
        assert response.status_code == 503

    def test_embedding_failure_returns_500(self, client, auth_headers):
        with (
            patch("app.api.routes.semantic_search.EmbeddingService") as mock_cls,
            _search_enabled(),
        ):
            svc = MagicMock()
            svc.is_available.return_value = True
            svc.generate_embedding = AsyncMock(return_value=None)
            mock_cls.return_value = svc
            response = client.get("/search/semantic?q=coffee", headers=auth_headers)
        assert response.status_code == 500

    def test_search_returns_results_structure(self, client, auth_headers, db):
        """With embeddings in DB, search should return proper response shape."""
        coop = Cooperative(name="Bio-Koop Cajamarca", embedding=_make_embedding())
        db.add(coop)
        db.commit()

        with (
            patch("app.api.routes.semantic_search.EmbeddingService") as mock_cls,
            _search_enabled(),
        ):
            svc = MagicMock()
            svc.is_available.return_value = True
            svc.generate_embedding = AsyncMock(return_value=_make_embedding())
            mock_cls.return_value = svc

            # Mock the raw SQL result so tests work on SQLite (no pgvector)
            with (
                patch(
                    "app.api.routes.semantic_search._search_cooperatives"
                ) as mock_search_coops,
                patch(
                    "app.api.routes.semantic_search._search_roasters"
                ) as mock_search_roasters,
            ):
                from app.schemas.semantic_search import SemanticSearchResult

                mock_search_coops.return_value = [
                    SemanticSearchResult(
                        entity_type="cooperative",
                        entity_id=coop.id,
                        name="Bio-Koop Cajamarca",
                        similarity_score=0.92,
                    )
                ]
                mock_search_roasters.return_value = []

                response = client.get(
                    "/search/semantic?q=Bio+Kaffee&entity_type=all&limit=10",
                    headers=auth_headers,
                )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Bio Kaffee"
        assert data["entity_type"] == "all"
        assert data["total"] == 1
        assert data["results"][0]["name"] == "Bio-Koop Cajamarca"
        assert data["results"][0]["similarity_score"] == pytest.approx(0.92)

    def test_search_cooperative_only(self, client, auth_headers):
        """entity_type=cooperative must not call _search_roasters."""
        with (
            patch("app.api.routes.semantic_search.EmbeddingService") as mock_cls,
            _search_enabled(),
            patch("app.api.routes.semantic_search._search_cooperatives") as mock_coops,
            patch("app.api.routes.semantic_search._search_roasters") as mock_roasters,
        ):
            svc = MagicMock()
            svc.is_available.return_value = True
            svc.generate_embedding = AsyncMock(return_value=_make_embedding())
            mock_cls.return_value = svc
            mock_coops.return_value = []
            mock_roasters.return_value = []

            client.get(
                "/search/semantic?q=test&entity_type=cooperative",
                headers=auth_headers,
            )
        mock_coops.assert_called_once()
        mock_roasters.assert_not_called()

    def test_search_roaster_only(self, client, auth_headers):
        """entity_type=roaster must not call _search_cooperatives."""
        with (
            patch("app.api.routes.semantic_search.EmbeddingService") as mock_cls,
            _search_enabled(),
            patch("app.api.routes.semantic_search._search_cooperatives") as mock_coops,
            patch("app.api.routes.semantic_search._search_roasters") as mock_roasters,
        ):
            svc = MagicMock()
            svc.is_available.return_value = True
            svc.generate_embedding = AsyncMock(return_value=_make_embedding())
            mock_cls.return_value = svc
            mock_coops.return_value = []
            mock_roasters.return_value = []

            client.get(
                "/search/semantic?q=test&entity_type=roaster",
                headers=auth_headers,
            )
        mock_roasters.assert_called_once()
        mock_coops.assert_not_called()

    def test_unauthenticated_returns_401(self, client):
        response = client.get("/search/semantic?q=test")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# /search/entity/{type}/{id}/similar tests
# ---------------------------------------------------------------------------


class TestSimilarEntities:
    """Tests for GET /search/entity/{type}/{id}/similar."""

    def test_invalid_entity_type_returns_400(self, client, auth_headers):
        response = client.get("/search/entity/unknown/1/similar", headers=auth_headers)
        assert response.status_code == 400

    def test_entity_not_found_returns_404(self, client, auth_headers, db):
        with _search_enabled():
            response = client.get(
                "/search/entity/cooperative/99999/similar",
                headers=auth_headers,
            )
        assert response.status_code == 404

    def test_entity_without_embedding_returns_404(self, client, auth_headers, db):
        coop = Cooperative(name="No Embedding Coop")
        db.add(coop)
        db.commit()
        db.refresh(coop)

        with _search_enabled():
            response = client.get(
                f"/search/entity/cooperative/{coop.id}/similar",
                headers=auth_headers,
            )
        assert response.status_code == 404
        assert "embedding" in response.json()["detail"].lower()

    def test_similar_entities_returned(self, client, auth_headers, db):
        coop = Cooperative(name="Anchor Coop", embedding=_make_embedding())
        neighbor = Cooperative(name="Neighbor Coop", embedding=_make_embedding())
        db.add_all([coop, neighbor])
        db.commit()
        db.refresh(coop)
        db.refresh(neighbor)

        with (
            _search_enabled(),
            patch("app.api.routes.semantic_search._search_cooperatives") as mock_search,
        ):
            from app.schemas.semantic_search import SemanticSearchResult

            # Return anchor + neighbor so anchor gets filtered out
            mock_search.return_value = [
                SemanticSearchResult(
                    entity_type="cooperative",
                    entity_id=coop.id,
                    name="Anchor Coop",
                    similarity_score=1.0,
                ),
                SemanticSearchResult(
                    entity_type="cooperative",
                    entity_id=neighbor.id,
                    name="Neighbor Coop",
                    similarity_score=0.88,
                ),
            ]

            response = client.get(
                f"/search/entity/cooperative/{coop.id}/similar?limit=5",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["entity_type"] == "cooperative"
        assert data["entity_id"] == coop.id
        assert data["entity_name"] == "Anchor Coop"
        # anchor itself should be excluded
        ids = [s["entity_id"] for s in data["similar_entities"]]
        assert coop.id not in ids
        assert neighbor.id in ids

    def test_similar_roasters_returned(self, client, auth_headers, db):
        roaster = Roaster(name="Anchor Roaster", embedding=_make_embedding())
        db.add(roaster)
        db.commit()
        db.refresh(roaster)

        with (
            _search_enabled(),
            patch("app.api.routes.semantic_search._search_roasters") as mock_search,
        ):
            mock_search.return_value = []

            response = client.get(
                f"/search/entity/roaster/{roaster.id}/similar",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["entity_type"] == "roaster"

    def test_unauthenticated_returns_401(self, client):
        response = client.get("/search/entity/cooperative/1/similar")
        assert response.status_code == 401
