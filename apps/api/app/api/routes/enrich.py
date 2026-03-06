from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
import structlog
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.schemas.enrichment import EnrichRequest, EnrichResponse
from app.services.enrichment import enrich_entity


router = APIRouter()
log = structlog.get_logger(__name__)


@router.post("/{entity_type}/{entity_id}", response_model=EnrichResponse)
def enrich(
    entity_type: str,
    entity_id: int,
    payload: EnrichRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
):
    if entity_type not in ("cooperative", "roaster"):
        raise HTTPException(
            status_code=400, detail=f"Invalid entity_type: {entity_type}"
        )
    try:
        out = enrich_entity(
            db,
            entity_type=entity_type,
            entity_id=entity_id,
            url=payload.url,
            use_llm=payload.use_llm,
        )
        return out
    except ValueError as e:
        log.warning(
            "enrich_request_invalid",
            error=str(e),
            entity_type=entity_type,
            entity_id=entity_id,
        )
        raise HTTPException(
            status_code=400, detail="Invalid enrichment request"
        )
