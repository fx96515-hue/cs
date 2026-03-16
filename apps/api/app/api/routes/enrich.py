from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Path
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
    entity_type: Literal["cooperative", "roaster"],
    entity_id: Annotated[int, Path(ge=1)],
    payload: EnrichRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
):
    try:
        out = enrich_entity(
            db,
            entity_type=entity_type,
            entity_id=entity_id,
            url=None,
            use_llm=payload.use_llm,
        )
        return out
    except ValueError:
        log.warning(
            "enrich_request_invalid",
            entity_type=entity_type,
            entity_id=entity_id,
        )
        raise HTTPException(
            status_code=400, detail="Invalid enrichment request"
        ) from None
    except Exception:
        log.error(
            "enrich_request_failed",
            entity_type=entity_type,
            entity_id=entity_id,
        )
        raise HTTPException(status_code=500, detail="Enrichment failed") from None
