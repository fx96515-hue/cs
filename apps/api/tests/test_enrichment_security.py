"""Security tests for enrichment error handling."""

from app.models.cooperative import Cooperative
from app.services.enrichment import enrich_entity


def test_enrich_entity_masks_internal_errors(db):
    """Returned errors must not leak internal exception details."""
    coop = Cooperative(name="Security Coop", website="http://127.0.0.1")
    db.add(coop)
    db.commit()
    db.refresh(coop)

    result = enrich_entity(
        db,
        entity_type="cooperative",
        entity_id=coop.id,
        url="http://127.0.0.1",
        use_llm=False,
    )

    assert result["status"] == "failed"
    assert result["error"] == "Enrichment failed"
