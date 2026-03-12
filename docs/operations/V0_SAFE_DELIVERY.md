# V0 Safe Delivery Flow

This repository uses a two-step delivery path for `v0` generated UI changes to avoid destabilizing `main`.

## Branch model

1. `ui/v0-sandbox`
2. reviewed feature branch (optional)
3. `main`

`v0` output must land in `ui/v0-sandbox` first. A follow-up PR then promotes approved changes to `main`.

## Guard rails

- `.github/workflows/v0-safety-gate.yml` blocks:
  - direct `v0-*` PRs to `main`
  - `v0` PRs that target anything except `ui/v0-sandbox`
  - `v0` PRs that modify files outside frontend/deploy scope
- `.github/CODEOWNERS` enforces code-owner review on UI/deploy files.
- Branch protection on `main` requires PR-based delivery.

## Allowed v0 scope

- `apps/web/**`
- `docs/ui/**`
- `vercel.json`
- `apps/web/vercel.json`
- `.github/workflows/vercel.yml`
- `.github/workflows/v0-safety-gate.yml`
- `.github/CODEOWNERS`
- `README.md`

## Vercel build stability

To avoid default static-output assumptions (for example expecting `public/`), this repo pins build settings in:

- `/vercel.json` (repo-root deployment case)
- `/apps/web/vercel.json` (app-root deployment case)

Both files define:

- `framework: nextjs`
- explicit install/build commands
- explicit output directory for Next.js build artifacts
