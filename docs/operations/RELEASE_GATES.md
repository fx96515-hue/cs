# Release Gates (Merge / Release)

Diese Gates müssen vor Merge in `main` bzw. vor Release erfüllt sein.

## P0 Gates (Pflicht)
- [ ] Backend Build/Start erfolgreich
- [ ] Frontend Build/Start erfolgreich
- [ ] API Health grün
- [ ] Frontend erreichbar
- [ ] DB/Redis Verbindung OK
- [ ] CI Basispipeline grün
- [ ] Keine offenen P0-Incidents ohne dokumentierte Ausnahme

## P1 Gates (Pflicht für sauberen Release)
- [ ] Lint / Typecheck grün
- [ ] Relevante Backend-Tests grün
- [ ] Relevante Frontend-Tests grün
- [ ] Docker Image Build erfolgreich
- [ ] Post-Deploy Health-Check definiert und grün
- [ ] Rollback-Plan dokumentiert

## P2 Gates (empfohlen)
- [ ] Security Scan ohne neue kritische Findings
- [ ] Observability/Alerts geprüft
- [ ] Doku/Versionsstand konsistent (CHANGELOG/STATUS/VERSION)
- [ ] Release Notes vorbereitet

## Ausnahmen
Ausnahmen sind nur erlaubt, wenn im PR dokumentiert:
- Was fehlt
- Risiko
- Zeitraum bis Nachbesserung
- Verantwortlicher Follow-up
