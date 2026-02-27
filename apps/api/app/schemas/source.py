from pydantic import BaseModel
from typing import Optional


class SourceCreate(BaseModel):
    name: str
    url: Optional[str] = None
    kind: str = "web"
    reliability: Optional[float] = None
    notes: Optional[str] = None


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    kind: Optional[str] = None
    reliability: Optional[float] = None
    notes: Optional[str] = None


class SourceOut(BaseModel):
    id: int
    name: str
    url: Optional[str] = None
    kind: str
    reliability: Optional[float] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True
