from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.news_item import NewsItem
from app.domains.news.schemas.news import NewsItemOut, NewsRefreshResponse
from app.domains.news.services.refresh import refresh_news

router = APIRouter()
ISO2_COUNTRY_PATTERN = r"^[A-Za-z]{2}$"


def _normalize_country_code(country: str) -> str:
    return country.strip().upper()


@router.get("/", response_model=list[NewsItemOut])
def list_news(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
    topic: Annotated[str, Query(min_length=1, max_length=100)] = "peru coffee",
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    days: Annotated[int, Query(ge=1, le=365)] = 7,
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    q = db.query(NewsItem).filter(NewsItem.topic == topic)
    q = q.filter((NewsItem.retrieved_at.is_(None)) | (NewsItem.retrieved_at >= cutoff))
    return q.order_by(NewsItem.retrieved_at.desc().nullslast()).limit(limit).all()


@router.post("/refresh", response_model=NewsRefreshResponse)
def refresh(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
    topic: Annotated[str, Query(min_length=1, max_length=100)] = "peru coffee",
    country: Annotated[str, Query(pattern=ISO2_COUNTRY_PATTERN)] = "PE",
    max_items: Annotated[int, Query(ge=1, le=200)] = 25,
):
    return refresh_news(
        db,
        topic=topic,
        country=_normalize_country_code(country),
        max_items=max_items,
    )
