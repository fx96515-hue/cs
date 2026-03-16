from pydantic import BaseModel


class KnowledgeDocOut(BaseModel):
    id: int
    category: str
    key: str
    title: str
    language: str
    content_md: str

    class Config:
        from_attributes = True


class KBSeedResponse(BaseModel):
    status: str
    created: int
    updated: int
