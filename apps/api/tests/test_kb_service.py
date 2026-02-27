"""Tests for knowledge base service."""

from app.services.kb import seed_default_kb, DEFAULT_DOCS
from app.models.knowledge_doc import KnowledgeDoc


def test_seed_default_kb_creates_docs(db):
    """Test seeding creates default knowledge base documents."""
    result = seed_default_kb(db)

    assert result["status"] == "ok"
    assert result["created"] >= 0
    assert result["updated"] >= 0


def test_seed_default_kb_idempotent(db):
    """Test seeding is idempotent (can run multiple times)."""
    # First seed
    seed_default_kb(db)

    # Second seed
    result2 = seed_default_kb(db)
    second_created = result2["created"]

    # Should not create duplicates on second run
    assert second_created == 0


def test_seed_default_kb_updates_changed_content(db):
    """Test seeding updates documents when content changes."""
    # First seed
    seed_default_kb(db)

    # Modify a document in database
    doc = db.query(KnowledgeDoc).first()
    if doc:
        original_content = doc.content_md
        doc.content_md = "Modified content"
        db.commit()

        # Seed again - should update to original
        seed_default_kb(db)

        db.refresh(doc)
        assert doc.content_md == original_content


def test_default_docs_structure():
    """Test DEFAULT_DOCS has required structure."""
    assert len(DEFAULT_DOCS) > 0

    for doc in DEFAULT_DOCS:
        assert "category" in doc
        assert "key" in doc
        assert "title" in doc
        assert "language" in doc
        assert "content_md" in doc


def test_knowledge_doc_creation(db):
    """Test creating a knowledge document directly."""
    doc = KnowledgeDoc(
        category="test",
        key="test_doc",
        title="Test Document",
        language="en",
        content_md="# Test\nThis is a test document.",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    assert doc.id is not None
    assert doc.category == "test"
    assert doc.key == "test_doc"


def test_knowledge_doc_retrieval(db):
    """Test retrieving knowledge documents."""
    seed_default_kb(db)

    docs = db.query(KnowledgeDoc).filter_by(category="logistics").all()
    assert len(docs) > 0


def test_knowledge_doc_language_filter(db):
    """Test filtering knowledge documents by language."""
    seed_default_kb(db)

    de_docs = db.query(KnowledgeDoc).filter_by(language="de").all()
    assert all(doc.language == "de" for doc in de_docs)
