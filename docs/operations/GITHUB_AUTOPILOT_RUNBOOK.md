# GitHub Autopilot Runbook

## Ziel
Workflow für: Audit -> Fix -> Test -> Commit -> Push -> PR

## Voraussetzungen
- `git` installiert
- `gh` installiert und eingeloggt (`gh auth login`)
- Repo lokal geklont
- Schreibrechte auf Repo
- Docker/Node/Python je nach Änderungen vorhanden

## Standardablauf (manuell)
1. Branch erstellen
2. Änderung umsetzen
3. Lokale Checks laufen lassen
4. Commit mit Conventional Commit
5. Branch pushen
6. PR erstellen
7. CI prüfen
8. Review + Squash Merge

## Standardablauf (Skripte)
### PowerShell
```powershell
.\scripts\automation\autopilot_pr.ps1 `
  -Branch "fix/production-health-backend" `
  -CommitMessage "fix: restore backend healthcheck startup path" `
  -PrTitle "fix: restore backend healthcheck startup path" `
  -IssueNumber 114 `
  -Labels "p0-critical,backend,production-alert"
```

### Bash
```bash
./scripts/automation/autopilot_pr.sh \
  --branch "fix/production-health-backend" \
  --commit "fix: restore backend healthcheck startup path" \
  --title "fix: restore backend healthcheck startup path" \
  --issue 114 \
  --labels "p0-critical,backend,production-alert"
```

## Branch Protection (empfohlen)
- PRs verpflichtend
- Status Checks verpflichtend
- Up-to-date Branch verpflichtend
- Direkt-Push auf `main` blockieren
- Auto-Merge optional erlauben

## Hinweise
- Skripte führen heuristische Checks aus und lassen sich repo-spezifisch erweitern.
- Bei P0 immer kleine PRs.
- Nach Merge: Doku/Version prüfen und ggf. nachziehen.
