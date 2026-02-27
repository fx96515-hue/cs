from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MarketObservationCreate(BaseModel):
    key: str
    value: float
    observed_at: datetime
    unit: Optional[str] = None
    currency: Optional[str] = None
    source_id: Optional[int] = None
    raw_text: Optional[str] = None
    meta: Optional[dict] = None


class MarketObservationOut(BaseModel):
    id: int
    key: str
    value: float
    unit: Optional[str] = None
    currency: Optional[str] = None
    observed_at: datetime
    source_id: Optional[int] = None
    raw_text: Optional[str] = None
    meta: Optional[dict] = None

    class Config:
        from_attributes = True
