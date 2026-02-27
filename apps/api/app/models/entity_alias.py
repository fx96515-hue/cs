from datetime import datetime
from sqlalchemy import String, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class EntityAlias(Base, TimestampMixin):
    """Aliases for an entity (cooperative/roaster).

    Used for dedup + search.
    """

    __tablename__ = "entity_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # cooperative|roaster
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )  # name|domain|social|other
    observed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "alias", name="uq_entity_alias"),
    )
