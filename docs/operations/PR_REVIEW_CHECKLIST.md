# PR Review Checkliste (Reviewer)

## Inhalt / Scope
- [ ] PR löst ein klares Problem
- [ ] Scope ist fokussiert (kein unnötiger Misch-PR)
- [ ] Risiken sind benannt

## Code / Qualität
- [ ] Änderungen sind nachvollziehbar
- [ ] Fehlerfälle sind berücksichtigt
- [ ] Kein offensichtlicher Dead Code / Debug-Code
- [ ] Typisierung / Validation konsistent

## Runtime / Ops
- [ ] Health/Smoke Auswirkungen bedacht
- [ ] Env/Config Änderungen dokumentiert
- [ ] Docker/Compose Auswirkungen klar

## Security
- [ ] Keine Secrets / Tokens / sensible Daten
- [ ] Auth/CORS/Headers (falls betroffen) sinnvoll
- [ ] Logging ohne Datenleck

## GitHub / Nachweise
- [ ] Commit-Historie sauber
- [ ] PR Template vollständig ausgefüllt
- [ ] CI grün
- [ ] Testnachweis plausibel
- [ ] Rollback beschrieben
