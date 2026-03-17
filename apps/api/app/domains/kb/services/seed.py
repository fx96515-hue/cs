from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.knowledge_doc import KnowledgeDoc


DEFAULT_DOCS: list[dict[str, Any]] = [
    {
        "category": "logistics",
        "key": "import_workflow_raw_coffee_de",
        "title": "Import-Workflow Rohkaffee (DE) - Checkliste",
        "language": "de",
        "content_md": (
            "**Hinweis**: Nur allgemeine Orientierung, keine Rechtsberatung.\\n\\n"
            "### Ziel\\n"
            "Rohkaffee (gruen) aus Peru in DE importieren, anschliessend Verkauf an Roestereien.\\n\\n"
            "### Minimaler Ablauf (high-level)\\n"
            "1. Lieferant verifizieren (Kooperative/Exporter, Dokumente, Referenzen)\\n"
            "2. Spezifikationen (Varietaeten, Processing, Ernte, Feuchte, Screen, Defects, SCA Score)\\n"
            "3. Muster: Cupping + Qualitaetsfreigabe\\n"
            "4. Vertrag/Incoterm (typisch FOB/CIF) + Payment Terms\\n"
            "5. Logistik buchen (Sea/Air), Versicherung, Inlandstrucking\\n"
            "6. Dokumente: Invoice, Packing List, Bill of Lading/AWB, ggf. Phytosanitary/COO\\n"
            "7. Zoll/Import in DE (Spediteur/Customs Broker) + Einfuhrumsatzsteuer\\n"
            "8. Ankunft/Quality Hold: Gewicht, Stichproben, Defect Check, Lagerung\\n"
            "9. Vertrieb: Preisschema, Samples an Roester, Kommunikation/CRM\\n\\n"
            "### CoffeeStudio Nutzung\\n"
            "- Kooperative/Roester: `status`, `next_action`, `evidence_count`\\n"
            "- Website/Deep Research: `/enrich/...` -> `web_extracts`\\n"
            "- News Radar: `/news/refresh`\\n"
            "- Landed Cost: `/logistics/landed-cost`\\n"
            "- Outreach: `/outreach/generate`\\n"
        ),
        "sources": {"note": "Fill with authoritative sources later"},
    }
]


def _insert_doc_postgres(db: Session, doc: dict[str, Any], language: str) -> bool:
    if not db.bind or db.bind.dialect.name != "postgresql":
        return False
    insert_stmt = (
        pg_insert(KnowledgeDoc)
        .values(**{**doc, "language": language})
        .on_conflict_do_nothing(constraint="uq_kb_cat_key_lang")
        .returning(KnowledgeDoc.id)
    )
    inserted_id = db.execute(insert_stmt).scalar_one_or_none()
    return inserted_id is not None


def _load_existing_doc(db: Session, doc: dict[str, Any], language: str) -> KnowledgeDoc | None:
    stmt = select(KnowledgeDoc).where(
        KnowledgeDoc.category == doc["category"],
        KnowledgeDoc.key == doc["key"],
        KnowledgeDoc.language == language,
    )
    return db.execute(stmt).scalar_one_or_none()


def _doc_has_changes(existing: KnowledgeDoc, doc: dict[str, Any]) -> bool:
    return (
        existing.content_md != doc["content_md"]
        or existing.title != doc["title"]
        or (existing.sources or {}) != (doc.get("sources") or {})
    )


def _apply_doc_update(existing: KnowledgeDoc, doc: dict[str, Any]) -> None:
    existing.title = doc["title"]
    existing.content_md = doc["content_md"]
    existing.sources = doc.get("sources")


def _seed_doc(db: Session, doc: dict[str, Any]) -> tuple[int, int]:
    language = doc.get("language", "de")
    if _insert_doc_postgres(db, doc, language):
        return 1, 0

    existing = _load_existing_doc(db, doc, language)
    if not existing:
        db.add(KnowledgeDoc(**{**doc, "language": language}))
        return 1, 0

    if _doc_has_changes(existing, doc):
        _apply_doc_update(existing, doc)
        return 0, 1
    return 0, 0


def seed_default_kb(db: Session) -> dict[str, Any]:
    created = 0
    updated = 0
    for doc in DEFAULT_DOCS:
        created_delta, updated_delta = _seed_doc(db, doc)
        created += created_delta
        updated += updated_delta

    db.commit()
    return {"status": "ok", "created": created, "updated": updated}
