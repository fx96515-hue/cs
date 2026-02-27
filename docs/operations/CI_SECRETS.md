# CI Secrets (GitHub Actions)

This file documents the repository secrets required by the enterprise CI workflows and recommended scopes.

Required secrets
- `SONAR_TOKEN` — SonarCloud token with project analyze permissions.
- `CODECOV_TOKEN` — Codecov upload token (if using Codecov).
- `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` — (or `GHCR_TOKEN`) for publishing images from workflows.
- `PYPI_API_TOKEN` — (optional) for publishing packages.
- `SLS_TOKEN` / `SENTRY_DSN` — (optional) for error reporting in CI.

Recommended setup steps
1. Go to the repository on GitHub → Settings → Secrets and variables → Actions → New repository secret.
2. Paste the token value and use the secret name above.
3. For `SONAR_TOKEN`, also ensure the SonarCloud organization has the project key matching this repo.

Notes on minimal scopes
- `SONAR_TOKEN`: token generated from SonarCloud user/account with 'Execute Analysis' rights.
- `CODECOV_TOKEN`: project token from Codecov; keep private.
- Docker registry tokens: only give push access for the specific repository/namespace.

CI troubleshooting
- If Sonar or Codecov steps fail with 401/403, verify the token in the UI and the repository/org membership for the token owner.
- For private registries: confirm the runner has network access to the registry and credentials are current.

Reference
- See `.github/workflows/sonarcloud.yml` and `.github/workflows/smoke-check.yml` for which secrets are referenced.
# CI Secrets Checklist

This document lists the repository secrets required to enable full CI, coverage and security scans.

Required GitHub Secrets

- `CODECOV_TOKEN`: Token for Codecov to upload coverage reports. Add via repo Settings → Secrets.
- `SONAR_TOKEN`: SonarCloud (or SonarQube) token for analysis upload.
- `DOCKER_REGISTRY_USER` / `DOCKER_REGISTRY_PASSWORD`: If CI pushes images to a private registry.
- `PYPI_API_TOKEN` (optional): For publishing Python packages if configured.

How to add
1. Go to repository Settings → Secrets → Actions
2. Add a new secret with name and value
3. Keep tokens secure; do not commit them into the repo

Notes
- After adding `CODECOV_TOKEN` and `SONAR_TOKEN`, re-run CI to populate badges and dashboards.
