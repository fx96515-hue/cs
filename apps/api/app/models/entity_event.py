from sqlalchemy import String, Integer, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class EntityEvent(Base, TimestampMixin):
    """Audit/event log for entity lifecycle.

    Examples: status_changed, enriched, web_checked, outreach_generated.
    """

    __tablename__ = "entity_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # cooperative|roaster
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)


Index("ix_entity_events_entity_type_id", EntityEvent.entity_type, EntityEvent.entity_id)
