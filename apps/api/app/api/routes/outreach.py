from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.schemas.outreach import OutreachRequest, OutreachResponse
from app.services.outreach import generate_outreach


router = APIRouter()


@router.post("/generate", response_model=OutreachResponse)
def generate(
    payload: OutreachRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    try:
        return generate_outreach(
            db,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            language=payload.language,  # type: ignore[arg-type]
            purpose=payload.purpose,  # type: ignore[arg-type]
            counterpart_name=payload.counterpart_name,
            refine_with_llm=payload.refine_with_llm,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
