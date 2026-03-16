from datetime import datetime, timedelta, timezone

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
    topic: str = Query("peru coffee", min_length=1, max_length=100),
    limit: int = Query(100, ge=1, le=500),
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst", "viewer")),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    q = db.query(NewsItem).filter(NewsItem.topic == topic)
    q = q.filter((NewsItem.retrieved_at.is_(None)) | (NewsItem.retrieved_at >= cutoff))
    return q.order_by(NewsItem.retrieved_at.desc().nullslast()).limit(limit).all()


@router.post("/refresh", response_model=NewsRefreshResponse)
def refresh(
    topic: str = Query("peru coffee", min_length=1, max_length=100),
    country: str = Query("PE", pattern=ISO2_COUNTRY_PATTERN),
    max_items: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "analyst")),
):
    return refresh_news(
        db,
        topic=topic,
        country=_normalize_country_code(country),
        max_items=max_items,
    )
