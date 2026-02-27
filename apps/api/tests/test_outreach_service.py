"""Tests for outreach service."""

import pytest
from unittest.mock import patch, MagicMock
from app.services.outreach import generate_outreach, _template
from app.models.cooperative import Cooperative
from app.models.roaster import Roaster


def test_generate_outreach_cooperative(db):
    """Test generating outreach for a cooperative."""
    coop = Cooperative(
        name="Test Cooperative",
        region="Cajamarca",
        website="https://testcoop.com",
        contact_email="info@testcoop.com",
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)

    result = generate_outreach(
        db,
        entity_type="cooperative",
        entity_id=coop.id,
        language="en",
        purpose="sourcing_pitch",
    )

    assert result["status"] == "ok"
    assert result["entity_type"] == "cooperative"
    assert result["entity_id"] == coop.id
    assert result["language"] == "en"
    assert result["purpose"] == "sourcing_pitch"
    assert "text" in result
    assert "Test Cooperative" in result["text"]


def test_generate_outreach_roaster(db):
    """Test generating outreach for a roaster."""
    roaster = Roaster(
        name="Test Roaster", city="Berlin", website="https://testroaster.com"
    )
    db.add(roaster)
    db.commit()
    db.refresh(roaster)

    result = generate_outreach(
        db,
        entity_type="roaster",
        entity_id=roaster.id,
        language="de",
        purpose="sourcing_pitch",
    )

    assert result["status"] == "ok"
    assert result["entity_type"] == "roaster"
    assert "Test Roaster" in result["text"]


def test_generate_outreach_invalid_entity_type(db):
    """Test generating outreach with invalid entity type."""
    with pytest.raises(ValueError, match="entity_type must be"):
        generate_outreach(db, entity_type="invalid", entity_id=1, language="en")


def test_generate_outreach_entity_not_found(db):
    """Test generating outreach for non-existent entity."""
    with pytest.raises(ValueError, match="entity not found"):
        generate_outreach(db, entity_type="cooperative", entity_id=99999, language="en")


def test_generate_outreach_with_llm_refinement(db):
    """Test generating outreach with LLM refinement."""
    coop = Cooperative(name="Test Cooperative", region="Cajamarca")
    db.add(coop)
    db.commit()
    db.refresh(coop)

    with (
        patch("app.services.outreach.settings") as mock_settings,
        patch("app.services.outreach.PerplexityClient") as mock_client_class,
    ):
        mock_settings.PERPLEXITY_API_KEY = "test_key"
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat_completions.return_value = "Refined text from LLM"

        result = generate_outreach(
            db,
            entity_type="cooperative",
            entity_id=coop.id,
            language="en",
            refine_with_llm=True,
        )

        assert result["used_llm"] is True
        assert result["text"] == "Refined text from LLM"


def test_template_sourcing_pitch_de():
    """Test German sourcing pitch template."""
    mock_entity = type(
        "obj",
        (object,),
        {
            "name": "Test Coop",
            "website": "https://test.com",
            "region": "Cajamarca",
            "contact_email": "info@test.com",
        },
    )

    text = _template(
        "de", purpose="sourcing_pitch", entity=mock_entity, counterpart="Max"
    )

    assert "Hallo Max" in text
    assert "Test Coop" in text
    assert "Peru" in text


def test_template_sample_request_en():
    """Test English sample request template."""
    mock_entity = type(
        "obj",
        (object,),
        {
            "name": "Test Roaster",
            "website": "https://test.com",
            "region": "Berlin",
            "contact_email": None,
        },
    )

    text = _template(
        "en", purpose="sample_request", entity=mock_entity, counterpart="Team"
    )

    assert "Hi Team" in text or "Hi team" in text
    assert "sample" in text.lower()


def test_template_spanish_language():
    """Test Spanish language template."""
    mock_entity = type(
        "obj",
        (object,),
        {"name": "Test Entity", "website": None, "region": None, "contact_email": None},
    )

    text = _template(
        "es", purpose="sourcing_pitch", entity=mock_entity, counterpart=None
    )

    assert "Hola" in text
    assert "Test Entity" in text
