from sqlalchemy import String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class Source(Base, TimestampMixin):
    """A data source (public URL, organization, etc.) with basic reliability metadata."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    kind: Mapped[str] = mapped_column(
        String(64), nullable=False, default="web"
    )  # web|api|internal|manual
    reliability: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0..1
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
