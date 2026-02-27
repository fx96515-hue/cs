from datetime import datetime
from pydantic import BaseModel


class NewsItemOut(BaseModel):
    id: int
    topic: str
    title: str
    url: str
    snippet: str | None = None
    country: str | None = None
    published_at: datetime | None = None
    retrieved_at: datetime | None = None

    class Config:
        from_attributes = True


class NewsRefreshResponse(BaseModel):
    status: str
    topic: str | None = None
    created: int | None = None
    updated: int | None = None
    errors: list[str] = []
