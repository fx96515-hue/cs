#!/usr/bin/env bash
set -euo pipefail

# Creates/updates common labels for the repo using GitHub CLI.
# Usage:
#   ./scripts/automation/create_labels.sh owner/repo
# or run inside the repo:
#   ./scripts/automation/create_labels.sh

REPO="${1:-}"
if [[ -z "$REPO" ]]; then
  REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
fi

declare -a LABELS=(
  "p0-critical|b60205|Kritischer Incident / Produktionsproblem"
  "p1-high|d93f0b|Hohe Priorität"
  "p2-medium|fbca04|Mittlere Priorität"
  "p3-low|0e8a16|Nice-to-have"
  "backend|1d76db|Backend / API"
  "frontend|5319e7|Frontend / UI"
  "infra|0052cc|Docker / Infra / Runtime"
  "ci-cd|c5def5|CI/CD und Workflows"
  "security|b60205|Security / Hardening"
  "docs|0e8a16|Dokumentation"
  "production-alert|e11d21|Produktion / Health Alarm"
  "hardening|f9d0c4|Qualität / Stabilisierung"
)

for item in "${LABELS[@]}"; do
  IFS='|' read -r name color desc <<< "$item"
  if gh label list --repo "$REPO" --search "$name" --json name -q '.[].name' | grep -qx "$name"; then
    gh label edit "$name" --repo "$REPO" --color "$color" --description "$desc"
    echo "Updated label: $name"
  else
    gh label create "$name" --repo "$REPO" --color "$color" --description "$desc"
    echo "Created label: $name"
  fi
done

echo "Done."
