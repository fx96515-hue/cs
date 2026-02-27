# Definition of Done (Engineering / PR)

Ein PR ist "Done", wenn **alle** relevanten Punkte erfüllt sind.

## 1) Funktional
- Problem reproduziert oder sauber beschrieben
- Ursache identifiziert
- Lösung implementiert
- Akzeptanzkriterien erfüllt

## 2) Qualität
- Lint grün (soweit vorhanden)
- Typecheck grün (Frontend/TS)
- Relevante Tests grün
- Build grün
- Keine offensichtlichen Regressionen

## 3) Runtime / Ops (wenn betroffen)
- Docker Compose Start erfolgreich
- Healthchecks grün (API / Frontend / Worker / DB / Redis soweit relevant)
- Logs ohne neue Fehlerflut
- Env-Dokumentation konsistent

## 4) Security
- Keine Secrets committed
- Konfiguration sicher (CORS/JWT/Headers wo relevant)
- Keine sensitiven Daten in Logs/PR
- Security-Hinweise berücksichtigt (falls betroffen)

## 5) GitHub / Review
- Branch nach Standard benannt
- Conventional Commit(s)
- PR-Beschreibung vollständig (Problem/Ursache/Lösung/Test/Risiko/Rollback)
- CI-Checks grün
- Reviewer kann Änderung nachvollziehen

## 6) Doku
- CHANGELOG / Status / README aktualisiert (wenn betroffen)
- Runbook/Setup angepasst (wenn Setup geändert wurde)
