from datetime import datetime
from pydantic import BaseModel


class ReportOut(BaseModel):
    id: int
    kind: str
    title: str | None = None
    report_at: datetime
    markdown: str
    payload: dict | None = None

    class Config:
        from_attributes = True
