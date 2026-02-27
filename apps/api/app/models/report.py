from datetime import datetime
from sqlalchemy import String, Text, JSON, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class Report(Base, TimestampMixin):
    """Generated reports (daily snapshots, etc.)."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="daily")
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    report_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    markdown: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)


Index("ix_reports_kind_report_at", Report.kind, Report.report_at)
