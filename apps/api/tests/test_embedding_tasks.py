"""Unit tests for Celery embedding tasks."""

from unittest.mock import AsyncMock, MagicMock, patch

from app.models.cooperative import Cooperative
from app.models.roaster import Roaster


def _make_embedding(dims: int = 384) -> list[float]:
    return [0.1] * dims


class TestGenerateEmbeddingsTask:
    """Tests for app.workers.tasks.generate_embeddings Celery task."""

    def test_skipped_when_provider_unavailable(self, db):
        """Task should return status=skipped when embedding provider is not available."""
        from app.workers.tasks import generate_embeddings

        svc = MagicMock()
        svc.is_available.return_value = False
        svc.provider_name = "local"

        result = self._run_task(generate_embeddings, db, svc)
        assert result["status"] == "skipped"
        assert "local" in result["reason"]

    def _run_task(self, task_fn, db, svc, **kwargs):
        """Helper: run a task with a mocked EmbeddingService and SessionLocal."""
        import app.services.embedding as emb_mod

        original_cls = emb_mod.EmbeddingService
        emb_mod.EmbeddingService = MagicMock(return_value=svc)  # type: ignore[misc]
        try:
            with patch("app.workers.tasks.SessionLocal", return_value=db):
                return task_fn(**kwargs)
        finally:
            emb_mod.EmbeddingService = original_cls  # type: ignore[misc]

    def test_generates_cooperative_embeddings(self, db):
        """Task should update embeddings for cooperatives lacking them."""
        coop = Cooperative(name="Coop Without Embedding")
        db.add(coop)
        db.commit()
        db.refresh(coop)

        from app.workers.tasks import generate_embeddings

        svc = MagicMock()
        svc.is_available.return_value = True
        svc.generate_entity_text.return_value = "Name: Coop Without Embedding"
        svc.generate_embeddings_batch = AsyncMock(return_value=[_make_embedding()])

        result = self._run_task(
            generate_embeddings, db, svc, entity_type="cooperative", batch_size=10
        )
        assert result["status"] == "ok"
        assert result["updated"]["cooperatives"] >= 1

    def test_generates_roaster_embeddings(self, db):
        """Task should update embeddings for roasters lacking them."""
        roaster = Roaster(name="Roaster Without Embedding")
        db.add(roaster)
        db.commit()
        db.refresh(roaster)

        from app.workers.tasks import generate_embeddings

        svc = MagicMock()
        svc.is_available.return_value = True
        svc.generate_entity_text.return_value = "Name: Roaster Without Embedding"
        svc.generate_embeddings_batch = AsyncMock(return_value=[_make_embedding()])

        result = self._run_task(
            generate_embeddings, db, svc, entity_type="roaster", batch_size=10
        )
        assert result["status"] == "ok"
        assert result["updated"]["roasters"] >= 1

    def test_skips_entities_with_existing_embeddings(self, db):
        """Entities that already have an embedding should NOT be re-embedded."""
        coop = Cooperative(name="Already Embedded", embedding=_make_embedding())
        db.add(coop)
        db.commit()

        from app.workers.tasks import generate_embeddings

        svc = MagicMock()
        svc.is_available.return_value = True
        svc.generate_embeddings_batch = AsyncMock(return_value=[])

        result = self._run_task(
            generate_embeddings, db, svc, entity_type="cooperative", batch_size=10
        )
        assert result["status"] == "ok"
        assert result["updated"]["cooperatives"] == 0
        # generate_embeddings_batch should not have been called (no entities found)
        svc.generate_embeddings_batch.assert_not_called()

    def test_processes_both_entity_types_when_none(self, db):
        """entity_type=None should process both cooperatives and roasters."""
        from app.workers.tasks import generate_embeddings

        svc = MagicMock()
        svc.is_available.return_value = True
        svc.generate_embeddings_batch = AsyncMock(return_value=[])

        result = self._run_task(
            generate_embeddings, db, svc, entity_type=None, batch_size=10
        )
        assert result["status"] == "ok"
        assert "cooperatives" in result["updated"]
        assert "roasters" in result["updated"]


class TestUpdateEntityEmbeddingTask:
    """Tests for app.workers.tasks.update_entity_embedding Celery task."""

    def _run_task(self, task_fn, db, svc, **kwargs):
        import app.services.embedding as emb_mod

        original_cls = emb_mod.EmbeddingService
        emb_mod.EmbeddingService = MagicMock(return_value=svc)  # type: ignore[misc]
        try:
            with patch("app.workers.tasks.SessionLocal", return_value=db):
                return task_fn(**kwargs)
        finally:
            emb_mod.EmbeddingService = original_cls  # type: ignore[misc]

    def test_skipped_when_provider_unavailable(self, db):
        from app.workers.tasks import update_entity_embedding

        svc = MagicMock()
        svc.is_available.return_value = False
        svc.provider_name = "openai"

        result = self._run_task(
            update_entity_embedding, db, svc, entity_type="cooperative", entity_id=1
        )
        assert result["status"] == "skipped"

    def test_entity_not_found_returns_error(self, db):
        from app.workers.tasks import update_entity_embedding

        svc = MagicMock()
        svc.is_available.return_value = True

        result = self._run_task(
            update_entity_embedding, db, svc, entity_type="cooperative", entity_id=99999
        )
        assert result["status"] == "error"

    def test_invalid_entity_type_returns_error(self, db):
        from app.workers.tasks import update_entity_embedding

        svc = MagicMock()
        svc.is_available.return_value = True

        result = self._run_task(
            update_entity_embedding, db, svc, entity_type="invalid_type", entity_id=1
        )
        assert result["status"] == "error"

    def test_updates_cooperative_embedding(self, db):
        coop = Cooperative(name="Coop To Update")
        db.add(coop)
        db.commit()
        db.refresh(coop)
        coop_id = coop.id  # capture before session may close

        from app.workers.tasks import update_entity_embedding

        svc = MagicMock()
        svc.is_available.return_value = True
        svc.generate_entity_embedding = AsyncMock(return_value=_make_embedding())

        result = self._run_task(
            update_entity_embedding,
            db,
            svc,
            entity_type="cooperative",
            entity_id=coop_id,
        )
        assert result["status"] == "ok"
        assert result["entity_type"] == "cooperative"
        assert result["entity_id"] == coop_id

    def test_updates_roaster_embedding(self, db):
        roaster = Roaster(name="Roaster To Update")
        db.add(roaster)
        db.commit()
        db.refresh(roaster)

        from app.workers.tasks import update_entity_embedding

        svc = MagicMock()
        svc.is_available.return_value = True
        svc.generate_entity_embedding = AsyncMock(return_value=_make_embedding())

        result = self._run_task(
            update_entity_embedding,
            db,
            svc,
            entity_type="roaster",
            entity_id=roaster.id,
        )
        assert result["status"] == "ok"
        assert result["entity_type"] == "roaster"

    def test_embedding_generation_failure_returns_error(self, db):
        coop = Cooperative(name="Fail Coop")
        db.add(coop)
        db.commit()
        db.refresh(coop)

        from app.workers.tasks import update_entity_embedding

        svc = MagicMock()
        svc.is_available.return_value = True
        svc.generate_entity_embedding = AsyncMock(return_value=None)

        result = self._run_task(
            update_entity_embedding,
            db,
            svc,
            entity_type="cooperative",
            entity_id=coop.id,
        )
        assert result["status"] == "error"
