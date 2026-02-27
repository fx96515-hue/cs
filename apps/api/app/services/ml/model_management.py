"""ML model management service."""

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ml_model import MLModel


class MLModelManagementService:
    """Service for managing ML model lifecycle."""

    def __init__(self, db: Session):
        self.db = db

    async def list_models(self, model_type: str | None = None) -> list[dict[str, Any]]:
        """List all ML models with metadata.

        Args:
            model_type: Optional filter by model type

        Returns:
            List of model metadata dictionaries
        """
        stmt = select(MLModel)

        if model_type:
            stmt = stmt.where(MLModel.model_type == model_type)

        stmt = stmt.order_by(MLModel.training_date.desc())

        result = self.db.execute(stmt)
        models = result.scalars().all()

        return [
            {
                "id": m.id,
                "model_name": m.model_name,
                "model_type": m.model_type,
                "algorithm": m.algorithm,
                "model_version": m.model_version,
                "training_date": m.training_date.isoformat(),
                "performance_metrics": m.performance_metrics,
                "training_data_count": m.training_data_count,
                "status": m.status,
            }
            for m in models
        ]

    async def get_active_model(self, model_type: str) -> dict[str, Any] | None:
        """Get currently active model for type.

        Args:
            model_type: Type of model to retrieve

        Returns:
            Model metadata dictionary or None
        """
        stmt = (
            select(MLModel)
            .where(MLModel.model_type == model_type)
            .where(MLModel.status == "active")
            .order_by(MLModel.training_date.desc())
            .limit(1)
        )
        result = self.db.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return {
            "id": model.id,
            "model_name": model.model_name,
            "model_type": model.model_type,
            "algorithm": model.algorithm,
            "model_version": model.model_version,
            "training_date": model.training_date.isoformat(),
            "features_used": model.features_used,
            "performance_metrics": model.performance_metrics,
            "training_data_count": model.training_data_count,
            "model_file_path": model.model_file_path,
            "status": model.status,
        }

    async def update_model_status(
        self, model_id: int, new_status: str
    ) -> dict[str, Any]:
        """Update model status.

        Args:
            model_id: ID of model to update
            new_status: New status (training, active, deprecated)

        Returns:
            Updated model metadata
        """
        stmt = select(MLModel).where(MLModel.id == model_id)
        result = self.db.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return {"status": "error", "message": "Model not found"}

        model.status = new_status
        self.db.commit()
        self.db.refresh(model)

        return {
            "status": "success",
            "model_id": model.id,
            "new_status": model.status,
        }

    async def trigger_model_retraining(self, model_type: str) -> dict[str, Any]:
        """Trigger model retraining job.

        This queues a Celery task for model retraining if sufficient new data is available.

        Args:
            model_type: Type of model to retrain ('freight_cost' or 'coffee_price')

        Returns:
            Job status dictionary with keys:
            - status: 'queued' if task started, 'skipped' if insufficient data
            - model_type: The model type requested
            - task_id: Celery task ID (only if status='queued')
            - message: Descriptive message
        """
        from app.workers.celery_app import celery
        from app.services.ml.training_pipeline import should_retrain

        # Check if retraining is needed
        needs_retrain = should_retrain(self.db, model_type, min_new_data=50)

        if not needs_retrain:
            return {
                "status": "skipped",
                "model_type": model_type,
                "message": "Not enough new data for retraining. Minimum 50 new records required.",
            }

        # Queue Celery task
        task = celery.send_task(
            "app.workers.tasks.train_ml_model",
            args=[model_type],
        )

        return {
            "status": "queued",
            "model_type": model_type,
            "task_id": task.id,
            "message": "Model retraining job queued successfully.",
        }

    async def get_model_performance(self, model_id: int) -> dict[str, Any] | None:
        """Get detailed performance metrics for a model.

        Args:
            model_id: ID of model to retrieve

        Returns:
            Performance metrics dictionary or None
        """
        stmt = select(MLModel).where(MLModel.id == model_id)
        result = self.db.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return {
            "model_id": model.id,
            "model_name": model.model_name,
            "model_type": model.model_type,
            "algorithm": model.algorithm,
            "training_date": model.training_date.isoformat(),
            "performance_metrics": model.performance_metrics,
            "training_data_count": model.training_data_count,
            "features_used": model.features_used,
        }
