from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.price_quote import PriceQuote
from app.domains.price_quotes.schemas.price_quote import (
    PriceQuoteCreate,
    PriceQuoteOut,
    PriceQuoteUpdate,
)

router = APIRouter()

NOT_FOUND_DETAIL = "Not found"
NOT_FOUND_RESPONSE: dict[int | str, dict[str, Any]] = {
    404: {"description": NOT_FOUND_DETAIL}
}


@router.get("/", response_model=list[PriceQuoteOut])
def list_price_quotes(
    lot_id: Annotated[int | None, Query(ge=1)] = None,
    deal_id: Annotated[int | None, Query(ge=1)] = None,
    source_id: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    *,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    q = db.query(PriceQuote)
    if lot_id is not None:
        q = q.filter(PriceQuote.lot_id == lot_id)
    if deal_id is not None:
        q = q.filter(PriceQuote.deal_id == deal_id)
    if source_id is not None:
        q = q.filter(PriceQuote.source_id == source_id)
    return q.order_by(PriceQuote.observed_at.desc()).limit(limit).all()


@router.post("/", response_model=PriceQuoteOut)
def create_price_quote(
    payload: PriceQuoteCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
):
    quote = PriceQuote(**payload.model_dump())
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


@router.get(
    "/{quote_id}",
    response_model=PriceQuoteOut,
    responses=NOT_FOUND_RESPONSE,
)
def get_price_quote(
    quote_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    quote = db.query(PriceQuote).filter(PriceQuote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    return quote


@router.patch(
    "/{quote_id}",
    response_model=PriceQuoteOut,
    responses=NOT_FOUND_RESPONSE,
)
def update_price_quote(
    quote_id: Annotated[int, Path(ge=1)],
    payload: PriceQuoteUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
):
    quote = db.query(PriceQuote).filter(PriceQuote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(quote, k, v)
    db.commit()
    db.refresh(quote)
    return quote


@router.delete("/{quote_id}", responses=NOT_FOUND_RESPONSE)
def delete_price_quote(
    quote_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin"))],
):
    quote = db.query(PriceQuote).filter(PriceQuote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
    db.delete(quote)
    db.commit()
    return {"status": "deleted"}
