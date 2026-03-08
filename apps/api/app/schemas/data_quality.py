from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DataQualityFlagOut(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    field_name: Optional[str] = None
    issue_type: str
    severity: str
    message: Optional[str] = None
    confidence: Optional[float] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    source_id: Optional[int] = None

    class Config:
        from_attributes = True
