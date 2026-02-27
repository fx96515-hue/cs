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
        "title": "Import-Workflow Rohkaffee (DE) Ã¢â‚¬â€ Checkliste",
        "language": "de",
        "content_md": (
            "**Hinweis**: Nur allgemeine Orientierung, keine Rechtsberatung.\\n\\n"
            "### Ziel\\n"
            "Rohkaffee (grÃƒÂ¼n) aus Peru in DE importieren, anschlieÃƒÅ¸end Verkauf an RÃƒÂ¶stereien.\\n\\n"
            "### Minimaler Ablauf (high-level)\\n"
            "1. Lieferant verifizieren (Kooperative/Exporter, Dokumente, Referenzen)\\n"
            "2. Spezifikationen (VarietÃƒÂ¤ten, Processing, Ernte, Feuchte, Screen, Defects, SCA Score)\\n"
            "3. Muster: Cupping + QualitÃƒÂ¤tsfreigabe\\n"
            "4. Vertrag/Incoterm (typisch FOB/CIF) + Payment Terms\\n"
            "5. Logistik buchen (Sea/Air), Versicherung, Inlandstrucking\\n"
            "6. Dokumente: Invoice, Packing List, Bill of Lading/AWB, ggf. Phytosanitary/COO\\n"
            "7. Zoll/Import in DE (Spediteur/Customs Broker) + Einfuhrumsatzsteuer\\n"
            "8. Ankunft/Quality Hold: Gewicht, Stichproben, Defect Check, Lagerung\\n"
            "9. Vertrieb: Preisschema, Samples an RÃƒÂ¶ster, Kommunikation/CRM\\n\\n"
            "### CoffeeStudio Nutzung\\n"
            "- Kooperative/RÃƒÂ¶ster: `status`, `next_action`, `evidence_count`\\n"
            "- Website/Deep Research: `/enrich/...` -> `web_extracts`\\n"
            "- News Radar: `/news/refresh`\\n"
            "- Landed Cost: `/logistics/landed-cost`\\n"
            "- Outreach: `/outreach/generate`\\n"
        ),
        "sources": {"note": "Fill with authoritative sources later"},
    }
]


def seed_default_kb(db: Session) -> dict[str, Any]:
    created = 0
    updated = 0
    for d in DEFAULT_DOCS:
        lang = d.get("language", "de")

        # Postgres: conflict-safe insert (idempotent under concurrency)
        if db.bind and db.bind.dialect.name == "postgresql":
            insert_stmt = (
                pg_insert(KnowledgeDoc)
                .values(**{**d, "language": lang})
                .on_conflict_do_nothing(constraint="uq_kb_cat_key_lang")
                .returning(KnowledgeDoc.id)
            )
            inserted_id = db.execute(insert_stmt).scalar_one_or_none()
            if inserted_id is not None:
                created += 1
                continue

        # Fallback / post-insert: fetch and update if changed
        stmt = select(KnowledgeDoc).where(
            KnowledgeDoc.category == d["category"],
            KnowledgeDoc.key == d["key"],
            KnowledgeDoc.language == lang,
        )
        existing = db.execute(stmt).scalar_one_or_none()
        if not existing:
            db.add(KnowledgeDoc(**{**d, "language": lang}))
            created += 1
        else:
            if (
                existing.content_md != d["content_md"]
                or existing.title != d["title"]
                or (existing.sources or {}) != (d.get("sources") or {})
            ):
                existing.title = d["title"]
                existing.content_md = d["content_md"]
                existing.sources = d.get("sources")
                updated += 1

    db.commit()
    return {"status": "ok", "created": created, "updated": updated}
