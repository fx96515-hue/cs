# CoffeeStudio GitHub Autopilot Paket

Dieses Paket enthält ein komplettes, copy/paste-fähiges Setup für einen GitHub-first Workflow:

- **Starker Master-Superprompt** (Audit + Fix + GitHub + PR + Release Gates)
- **3 Varianten-Prompts**
  - Audit-Only
  - Coding-Agent
  - Autopilot-PR
- **GitHub Templates**
  - Pull Request Template
  - Issue Templates (P0 Bug + Hardening Task)
- **Ops/Engineering Doku**
  - Definition of Done
  - Release Gates
  - PR Review Checkliste
  - Branching & Commit Regeln
  - GitHub Autopilot Runbook
  - Branch Protection Empfehlungen
- **Automations-Skripte**
  - `autopilot_pr.ps1`
  - `autopilot_pr.sh`
  - Label-Setup Skripte

## Empfohlener Einsatz (dein Wunsch-Flow)
1. Du gibst dem Agenten den **Master-Superprompt** oder **Autopilot-PR Prompt**
2. Du sagst: **"Ja, mach P0 Production Health zuerst"**
3. Agent arbeitet lokal:
   - Audit -> Fix -> Test -> Commit -> Push -> PR
4. Du prüfst PR auf GitHub
5. Merge (Squash) wenn CI grün

## Voraussetzungen (lokal)
- `git`
- `gh` (GitHub CLI) + `gh auth login`
- Python/Node/Docker (je nach Repo-Checks)
- Schreibrechte auf das Repo

## Hinweise
- Skripte sind bewusst generisch gehalten und können leicht an eure tatsächlichen CI-Kommandos angepasst werden.
- `autopilot_pr.*` führen lokale Checks heuristisch aus (wenn Dateien/Ordner vorhanden sind).
- Branch Protection wird in GitHub (UI oder gh/api) konfiguriert.
