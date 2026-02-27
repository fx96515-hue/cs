"""Semantic search API endpoints using pgvector embeddings."""

from __future__ import annotations

import structlog
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.core.config import settings
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster
from app.schemas.semantic_search import (
    SemanticSearchResponse,
    SemanticSearchResult,
    SimilarEntityResponse,
    SimilarEntityResult,
)
import app.services.embedding as embedding_service

# Alias for patching in tests without importing a mutable attribute directly.
EmbeddingService = embedding_service.EmbeddingService

router = APIRouter(prefix="/search", tags=["semantic-search"])
log = structlog.get_logger()


def _require_search_enabled() -> None:
    """Raise 503 when the semantic-search feature flag is off."""
    if not settings.SEMANTIC_SEARCH_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Semantic search is disabled (SEMANTIC_SEARCH_ENABLED=false).",
        )


@router.get("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    q: Annotated[str, Query(min_length=1, max_length=500)],
    entity_type: Annotated[str, Query()] = "all",
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Search for entities using semantic similarity.

    Args:
        q: Search query text
        entity_type: Type to search ('cooperative', 'roaster', or 'all')
        limit: Maximum results to return (default 10, max 50)
        db: Database session
        _: Authentication dependency

    Returns:
        Semantic search results with similarity scores
    """
    _require_search_enabled()
    service = EmbeddingService()

    # Check if service is available
    if not service.is_available():
        log.warning(
            "semantic_search_unavailable",
            provider=service.provider_name,
            reason="embedding_provider_unavailable",
        )
        raise HTTPException(
            status_code=503,
            detail=(
                "Semantic search is not available. "
                f"Embedding provider '{service.provider_name}' is not configured. "
                "Install sentence-transformers or set OPENAI_API_KEY."
            ),
        )

    # Generate query embedding
    query_embedding = await service.generate_embedding(q)
    if not query_embedding:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate query embedding",
        )

    results: list[SemanticSearchResult] = []

    # Search cooperatives
    if entity_type in ("all", "cooperative"):
        coop_results = _search_cooperatives(db, query_embedding, limit)
        results.extend(coop_results)

    # Search roasters
    if entity_type in ("all", "roaster"):
        roaster_results = _search_roasters(db, query_embedding, limit)
        results.extend(roaster_results)

    # Sort by similarity and limit
    results.sort(key=lambda x: x.similarity_score, reverse=True)
    results = results[:limit]

    log.info(
        "semantic_search_completed",
        query=q,
        entity_type=entity_type,
        results_count=len(results),
    )

    return SemanticSearchResponse(
        query=q,
        entity_type=entity_type,
        results=results,
        total=len(results),
    )


@router.get("/entity/{entity_type}/{entity_id}/similar")
async def find_similar_entities(
    entity_type: str,
    entity_id: int,
    limit: Annotated[int, Query(ge=1, le=50)] = 5,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    """Find similar entities based on embedding similarity.

    Args:
        entity_type: 'cooperative' or 'roaster'
        entity_id: ID of the entity to find similar entities for
        limit: Maximum results to return (default 5, max 50)
        db: Database session
        _: Authentication dependency

    Returns:
        Similar entities with similarity scores
    """
    if entity_type not in ("cooperative", "roaster"):
        raise HTTPException(status_code=400, detail="Invalid entity_type")

    _require_search_enabled()

    # Get entity and check if it has embedding
    entity: Cooperative | Roaster | None
    if entity_type == "cooperative":
        entity = db.query(Cooperative).filter(Cooperative.id == entity_id).first()
    else:
        entity = db.query(Roaster).filter(Roaster.id == entity_id).first()

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    if entity.embedding is None:
        raise HTTPException(
            status_code=404,
            detail="Entity does not have an embedding yet. Please generate embeddings first.",
        )

    # Search for similar entities
    if entity_type == "cooperative":
        similar = _search_cooperatives(
            db, entity.embedding, limit + 1
        )  # +1 to exclude self
        # Filter out the entity itself
        similar = [s for s in similar if s.entity_id != entity_id][:limit]
    else:
        similar = _search_roasters(
            db, entity.embedding, limit + 1
        )  # +1 to exclude self
        similar = [s for s in similar if s.entity_id != entity_id][:limit]

    log.info(
        "similar_entities_found",
        entity_type=entity_type,
        entity_id=entity_id,
        similar_count=len(similar),
    )

    return SimilarEntityResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity.name,
        similar_entities=[
            SimilarEntityResult(
                entity_id=r.entity_id,
                name=r.name,
                similarity_score=r.similarity_score,
                region=r.region,
                city=r.city,
                certifications=r.certifications,
                total_score=r.total_score,
            )
            for r in similar
        ],
        total=len(similar),
    )


def _search_cooperatives(
    db: Session, query_embedding: list[float], limit: int
) -> list[SemanticSearchResult]:
    """Search cooperatives using cosine similarity.

    Args:
        db: Database session
        query_embedding: Query embedding vector
        limit: Maximum results

    Returns:
        List of search results
    """
    # Use pgvector's cosine similarity operator (<=>)
    # Note: <=> returns distance (0 = identical, 2 = opposite)
    # We convert to similarity: 1 - (distance / 2)
    query = text(
        """
        SELECT 
            id, 
            name, 
            region, 
            certifications, 
            total_score,
            1 - (embedding <=> :query_embedding) AS similarity
        FROM cooperatives
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> :query_embedding
        LIMIT :limit
        """
    )

    rows = db.execute(
        query,
        {
            "query_embedding": query_embedding,
            "limit": limit,
        },
    ).fetchall()

    return [
        SemanticSearchResult(
            entity_type="cooperative",
            entity_id=row[0],
            name=row[1],
            region=row[2],
            certifications=row[3],
            total_score=row[4],
            similarity_score=max(0.0, min(1.0, row[5])),  # Clamp to [0, 1]
        )
        for row in rows
    ]


def _search_roasters(
    db: Session, query_embedding: list[float], limit: int
) -> list[SemanticSearchResult]:
    """Search roasters using cosine similarity.

    Args:
        db: Database session
        query_embedding: Query embedding vector
        limit: Maximum results

    Returns:
        List of search results
    """
    query = text(
        """
        SELECT 
            id, 
            name, 
            city, 
            total_score,
            1 - (embedding <=> :query_embedding) AS similarity
        FROM roasters
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> :query_embedding
        LIMIT :limit
        """
    )

    rows = db.execute(
        query,
        {
            "query_embedding": query_embedding,
            "limit": limit,
        },
    ).fetchall()

    return [
        SemanticSearchResult(
            entity_type="roaster",
            entity_id=row[0],
            name=row[1],
            city=row[2],
            total_score=row[3],
            similarity_score=max(0.0, min(1.0, row[4])),  # Clamp to [0, 1]
        )
        for row in rows
    ]
