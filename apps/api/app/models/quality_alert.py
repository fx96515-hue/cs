from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class QualityAlert(Base, TimestampMixin):
    """Quality alerts for tracking score changes and certifications."""

    __tablename__ = "quality_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # cooperative|roaster
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # score_drop|score_improvement|new_certification|certification_lost
    field_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    old_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, default="info", index=True
    )  # info|warning|critical
    acknowledged: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    acknowledged_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


Index(
    "ix_quality_alerts_entity_type_id", QualityAlert.entity_type, QualityAlert.entity_id
)
Index(
    "ix_quality_alerts_severity_ack", QualityAlert.severity, QualityAlert.acknowledged
)
