from pydantic import BaseModel


class PeruRegionOut(BaseModel):
    id: int
    code: str
    name: str
    description_de: str | None = None
    altitude_range: str | None = None
    typical_varieties: str | None = None
    typical_processing: str | None = None
    logistics_notes: str | None = None
    risk_notes: str | None = None

    class Config:
        from_attributes = True
