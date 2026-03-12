from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
import structlog
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.schemas.enrichment import EnrichRequest, EnrichResponse
from app.services.enrichment import enrich_entity


router = APIRouter()
log = structlog.get_logger(__name__)
ENRICH_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"description": "Invalid enrichment request"},
    500: {"description": "Enrichment failed"},
}


@router.post(
    "/{entity_type}/{entity_id}",
    response_model=EnrichResponse,
    responses=ENRICH_ERROR_RESPONSES,
)
def enrich(
    entity_type: str,
    entity_id: int,
    payload: EnrichRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
):
    if entity_type not in ("cooperative", "roaster"):
        raise HTTPException(status_code=400, detail="Invalid entity_type")
    try:
        out = enrich_entity(
            db,
            entity_type=entity_type,
            entity_id=entity_id,
            url=None,
            use_llm=payload.use_llm,
        )
        return out
    except ValueError as e:
        log.warning(
            "enrich_request_invalid",
            error_type=type(e).__name__,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        raise HTTPException(status_code=400, detail="Invalid enrichment request")
    except Exception as e:
        log.error(
            "enrich_request_failed",
            error_type=type(e).__name__,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        raise HTTPException(status_code=500, detail="Enrichment failed")
