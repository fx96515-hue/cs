from sqlalchemy import String, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class KnowledgeDoc(Base, TimestampMixin):
    """Small internal KB documents (logistics, customs, checklists).

    Content is informational and intentionally editable.
    """

    __tablename__ = "knowledge_docs"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="de")
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint("category", "key", "language", name="uq_kb_cat_key_lang"),
    )
