from datetime import datetime
from sqlalchemy import String, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin


class MLModel(Base, TimestampMixin):
    """Metadata for trained ML models."""

    __tablename__ = "ml_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # freight_prediction, price_prediction
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    training_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    features_used: Mapped[dict] = mapped_column(JSON, nullable=False)
    performance_metrics: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )  # mae, rmse, r2_score, accuracy_percentage
    training_data_count: Mapped[int] = mapped_column(Integer, nullable=False)
    model_file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # training, active, deprecated
    algorithm: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )  # random_forest, xgboost
