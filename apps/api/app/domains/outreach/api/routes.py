from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.domains.outreach.schemas.outreach import OutreachRequest, OutreachResponse
from app.domains.outreach.services.generator import generate_outreach


router = APIRouter()


@router.post(
    "/generate",
    response_model=OutreachResponse,
    responses={400: {"description": "Invalid request"}},
)
def generate(
    payload: OutreachRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[object, Depends(require_role("admin", "analyst", "viewer"))],
):
    try:
        return generate_outreach(
            db,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            language=payload.language,
            purpose=payload.purpose,
            counterpart_name=payload.counterpart_name,
            refine_with_llm=payload.refine_with_llm,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request")
