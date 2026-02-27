from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.schemas.enrichment import EnrichRequest, EnrichResponse
from app.services.enrichment import enrich_entity


router = APIRouter()


@router.post("/{entity_type}/{entity_id}", response_model=EnrichResponse)
def enrich(
    entity_type: str,
    entity_id: int,
    payload: EnrichRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
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
        raise HTTPException(status_code=400, detail=str(e))
