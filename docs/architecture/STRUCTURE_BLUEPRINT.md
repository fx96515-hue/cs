# CoffeeStudio Struktur-Blueprint (Enterprise)

## Ist-Zustand (Kurz)
- API ist technisch stabil, aber historisch schichtenorientiert (`api/routes`, `services`, `schemas`) mit wachsender Querschnittslogik.
- Assistant-Logik war auf mehrere Orte verteilt (Chat + RAG-Analyst + LLM-Provider) und teilweise mit Legacy-Pfaden gekoppelt.
- Web hat bereits eine gute UI-Richtung, aber heterogene Feature-Struktur und einzelne Legacy-Routen.

## Zielbild
- Domänenorientierte Kernbereiche in API und Web.
- Alte Pfade bleiben nur als dünne Kompatibilitätsschicht.
- Klare Trennung: API-Adapter, Domänen-Service, Schema/Contracts, Provider/Infra.

## Geplante Zielstruktur (API)
- `app/domains/<domain>/api/`
- `app/domains/<domain>/services/`
- `app/domains/<domain>/schemas/`
- `app/domains/<domain>/providers/` (wenn domänenspezifisch)
- `app/api/routes/*` nur als stabile Entry-Adapter oder Import-Fassade.

## Bereits umgesetzt (dieser Slice)
- Neue Domain `app/domains/assistant/` angelegt.
- Assistant- und RAG-Analyst-Implementierung in die Domain gespiegelt:
  - `domains/assistant/api/chat_routes.py`
  - `domains/assistant/api/analyst_routes.py`
  - `domains/assistant/services/chat_service.py`
  - `domains/assistant/services/analyst_service.py`
  - `domains/assistant/schemas/chat.py`
  - `domains/assistant/schemas/analyst.py`
- Alte Pfade (`app/api/routes/*`, `app/services/*`, `app/schemas/*`) auf Kompatibilitäts-Wrapper reduziert.

## Nächste Slices (ohne Big-Bang)
1. Assistant-Domain abschließen
- LLM-Provider-Selektion in Domain kapseln (aktuell noch global in `services/llm_providers.py`).
- Domain-Tests unter `apps/api/tests/domains/assistant/` konsolidieren.
- Kodierungs-/Meldungstexte weiter normalisieren.

2. API-Domain-Rollout (inkrementell)
- `news`, `reports`, `outreach`, `peru_sourcing` als nächste Domänen migraten.
- Je Domäne: erst Spiegelung + Wrapper, dann interne Imports umstellen.

3. Web-Struktur angleichen
- Feature-Ordner unter `app/features/*` vorbereiten, bestehende Seiten nur umleiten.
- Legacy `/ki` final entfernen, sobald Redirect-Zeitfenster abgeschlossen ist.

4. Repo-Hygiene
- lokale Artefakte/Caches strikt aus Build-Kontext halten.
- ungenutzte Kompatibilitätspfade nach stabiler Übergangsphase entfernen.

## Qualitätsregeln pro Slice
- Keine direkte Breaking-Änderung.
- Vollständige Gates grün vor Commit.
- Alte Importpfade erst entfernen, wenn keine Referenzen mehr existieren.
