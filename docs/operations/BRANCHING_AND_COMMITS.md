# Branching & Commits Standard

## Branch-Schema
- `fix/<kurzbeschreibung>`
- `feat/<kurzbeschreibung>`
- `chore/<kurzbeschreibung>`
- `docs/<kurzbeschreibung>`
- `refactor/<kurzbeschreibung>`
- `test/<kurzbeschreibung>`

Beispiele:
- `fix/production-health-backend`
- `fix/frontend-api-baseurl`
- `chore/ci-release-gates`
- `docs/status-version-sync`

## Commit-Konvention (Conventional Commits)
- `fix: ...`
- `feat: ...`
- `chore: ...`
- `docs: ...`
- `refactor: ...`
- `test: ...`

Beispiele:
- `fix: restore backend healthcheck startup path`
- `fix: align frontend API base URL for docker runtime`
- `chore: normalize env defaults for local stack`
- `docs: sync changelog and status version markers`

## Commit-Regeln
1. Klein und reviewbar halten
2. Ein Commit = ein klarer Zweck
3. Keine WIP-Commits in PRs
4. Kein Commit mit Secrets / Tokens / .env
5. Wenn relevant Issue referenzieren (`#114`)

## Merge-Strategie
Standard: **Squash Merge**
- hält Historie sauber
- passt gut zu mehreren kleinen Commits im Fix-Branch
