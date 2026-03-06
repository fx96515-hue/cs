from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.price_quote import PriceQuote
from app.schemas.price_quote import PriceQuoteCreate, PriceQuoteOut, PriceQuoteUpdate

router = APIRouter()


@router.get("/", response_model=list[PriceQuoteOut])
def list_price_quotes(
    lot_id: int | None = None,
    deal_id: int | None = None,
    source_id: int | None = None,
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
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
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    quote = PriceQuote(**payload.model_dump())
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


@router.get("/{quote_id}", response_model=PriceQuoteOut)
def get_price_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    quote = db.query(PriceQuote).filter(PriceQuote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Not found")
    return quote


@router.patch("/{quote_id}", response_model=PriceQuoteOut)
def update_price_quote(
    quote_id: int,
    payload: PriceQuoteUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    quote = db.query(PriceQuote).filter(PriceQuote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(quote, k, v)
    db.commit()
    db.refresh(quote)
    return quote


@router.delete("/{quote_id}")
def delete_price_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    quote = db.query(PriceQuote).filter(PriceQuote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(quote)
    db.commit()
    return {"status": "deleted"}
