# CI Secrets

This file documents repository-level secrets and variables used by GitHub Actions workflows.

## Required for Core CI
- `SONAR_TOKEN`: token for SonarQube/SonarCloud scan upload.
- `SONAR_PROJECT_KEY` (repository variable): project key used by Sonar scanner.
- `SONAR_ORGANIZATION` (repository variable): required when using SonarCloud.
- `CODECOV_TOKEN` (optional): enables Codecov coverage upload if configured.

## Required for Docker Image Publishing
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`

If Docker Hub credentials are not set, workflows still publish to GHCR where configured.

## Required for Vercel Deploy Workflow
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

When these are missing, `.github/workflows/vercel.yml` exits cleanly with a skip message.

## Optional Sonar Variables
- `SONAR_HOST_URL` (secret, for self-hosted SonarQube; defaults to `https://sonarcloud.io` when not set)
- `SONAR_BRANCH`, `SONAR_SEVERITIES`, `SONAR_STATUSES`, `SONAR_MAX_CREATE`, `SONAR_LABEL`, `SONAR_AUTO_CLOSE` (used by Sonar issues sync workflow)

## Notes
- Add secrets under: `Repository Settings -> Secrets and variables -> Actions`.
- Add non-secret parameters (for example `SONAR_PROJECT_KEY`) under repository variables.
- For pull requests from forks, secrets are intentionally unavailable; optional workflows are skipped by design.
