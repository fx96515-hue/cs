#!/usr/bin/env bash
set -euo pipefail

BRANCH=""
COMMIT_MSG=""
PR_TITLE=""
ISSUE_NUMBER=""
LABELS=""
DRAFT="false"
SKIP_CHECKS="false"
PR_BODY_FILE=""

usage() {
  cat <<EOF
Usage:
  ./scripts/automation/autopilot_pr.sh \
    --branch "fix/..." \
    --commit "fix: ..." \
    --title "fix: ..." \
    [--issue 114] \
    [--labels "p0-critical,backend"] \
    [--draft] \
    [--skip-checks] \
    [--body-file path/to/body.md]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch) BRANCH="$2"; shift 2 ;;
    --commit) COMMIT_MSG="$2"; shift 2 ;;
    --title) PR_TITLE="$2"; shift 2 ;;
    --issue) ISSUE_NUMBER="$2"; shift 2 ;;
    --labels) LABELS="$2"; shift 2 ;;
    --draft) DRAFT="true"; shift ;;
    --skip-checks) SKIP_CHECKS="true"; shift ;;
    --body-file) PR_BODY_FILE="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

[[ -n "$BRANCH" ]] || { echo "Missing --branch"; exit 1; }
[[ -n "$COMMIT_MSG" ]] || { echo "Missing --commit"; exit 1; }
[[ -n "$PR_TITLE" ]] || { echo "Missing --title"; exit 1; }

run() {
  echo "==> $1"
  shift
  "$@"
}

assert_clean_git_state() {
  if [[ -n "$(git status --porcelain)" ]]; then
    echo "Working tree is not clean. Please commit/stash first." >&2
    exit 1
  fi
}

heuristic_checks() {
  if [[ "$SKIP_CHECKS" == "true" ]]; then
    echo "Checks skipped (--skip-checks)."
    return
  fi

  if [[ -f frontend/package.json ]]; then
    pushd frontend >/dev/null
    if [[ -f package-lock.json || -f npm-shrinkwrap.json ]]; then
      npm ci || true
    fi
    npm run lint || true
    npm run typecheck || true
    npm run build || true
    popd >/dev/null
  fi

  if [[ -f backend/requirements.txt || -f backend/pyproject.toml ]]; then
    pushd backend >/dev/null
    if [[ -f requirements.txt ]]; then
      python -m pip install -r requirements.txt || true
    fi
    python -m pytest || true
    popd >/dev/null
  fi

  if [[ -f docker-compose.yml ]]; then
    docker compose -f docker-compose.yml config || true
  elif [[ -f compose.yml ]]; then
    docker compose -f compose.yml config || true
  fi
}

build_pr_body() {
  local f="$1"
  if [[ -n "$f" && -f "$f" ]]; then
    cat "$f"
    return
  fi
  local issueLine="-"
  if [[ -n "$ISSUE_NUMBER" ]]; then issueLine="Bezug: #$ISSUE_NUMBER"; fi
  cat <<EOF
## Problem
- <kurz beschreiben>
- $issueLine

## Ursache
- <Root Cause>

## Lösung
- <Umsetzung>

## Betroffene Bereiche
- [ ] Backend
- [ ] Frontend
- [ ] Infra/CI
- [ ] Doku
- [ ] Security

## Testnachweis
- [ ] Lint
- [ ] Typecheck
- [ ] Tests
- [ ] Build
- [ ] Smoke/Health lokal
- [ ] Docker Compose Start (falls relevant)

## Risiken
- <Risiko>

## Rollback
- Revert PR / Branch

## Doku-Updates
- [ ] CHANGELOG
- [ ] STATUS / Operations Doku
- [ ] README
- [ ] Keine Doku-Änderung nötig

## Follow-ups
- <optional>
EOF
}

run "GitHub auth check" gh auth status
assert_clean_git_state
run "Create branch" git checkout -b "$BRANCH"

heuristic_checks

run "git add" git add -A
run "git commit" git commit -m "$COMMIT_MSG"
run "git push" git push -u origin "$BRANCH"

tmp_body="$(mktemp)"
build_pr_body "$PR_BODY_FILE" > "$tmp_body"

if [[ "$DRAFT" == "true" ]]; then
  run "Create PR" gh pr create --title "$PR_TITLE" --body-file "$tmp_body" --draft
else
  run "Create PR" gh pr create --title "$PR_TITLE" --body-file "$tmp_body"
fi

if [[ -n "$LABELS" ]]; then
  pr_number="$(gh pr view --json number -q .number)"
  IFS=',' read -ra arr <<< "$LABELS"
  for l in "${arr[@]}"; do
    l_trimmed="$(echo "$l" | xargs)"
    [[ -n "$l_trimmed" ]] && gh pr edit "$pr_number" --add-label "$l_trimmed" || true
  done
fi

echo
echo "✅ Autopilot PR flow complete."
echo "Now review on GitHub: files changed, CI checks, PR text, and merge readiness."
