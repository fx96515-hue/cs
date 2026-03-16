from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.knowledge_doc import KnowledgeDoc
from app.domains.kb.schemas.kb import KnowledgeDocOut, KBSeedResponse
from app.domains.kb.services.seed import seed_default_kb


router = APIRouter()


@router.get("/", response_model=list[KnowledgeDocOut])
def list_kb(
    category: str = "logistics",
    language: str = "de",
    *,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    q = db.query(KnowledgeDoc).filter(
        KnowledgeDoc.category == category, KnowledgeDoc.language == language
    )
    return q.order_by(KnowledgeDoc.title.asc()).all()


@router.post("/seed", response_model=KBSeedResponse)
def seed(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
):
    return seed_default_kb(db)
