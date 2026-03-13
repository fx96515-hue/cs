# SonarQube / SonarCloud Integration

This repository uses `.github/workflows/sonar.yml` for optional Sonar analysis.

## Workflow Behavior
- Runs on `push` to `main`, PR updates, and manual dispatch.
- Automatically skips (green) when required Sonar credentials are missing.
- Runs API tests with coverage and uploads coverage-aware scan results.
- Enforces a focused gate on PRs: fails only when **new code** introduces unresolved
  `BLOCKER`/`CRITICAL` issues or `VULNERABILITY` findings.

## Required Configuration
- Secret: `SONAR_TOKEN`
- Variable: `SONAR_PROJECT_KEY`
- Variable: `SONAR_ORGANIZATION` (required when using SonarCloud host)

## Optional Configuration
- Secret: `SONAR_HOST_URL` (set for self-hosted SonarQube; defaults to SonarCloud URL if absent)

## SonarCloud Note
- The workflow disables SonarCloud Automatic Analysis via API before CI scan.
- `SONAR_TOKEN` must have permission to administer the SonarCloud project.

## Sonar Issue Sync
- `.github/workflows/sonar_issues_sync.yml` syncs Sonar issues into GitHub issues.
- Sync is **disabled by default** and only runs when `SONAR_ISSUE_SYNC_ENABLED=true`.
- Default sync behavior is intentionally conservative:
  - severities: `BLOCKER,CRITICAL`
  - statuses: `OPEN,REOPENED`
  - max new issues per run: `5`
  - auto-close resolved issues: enabled

## References
- SonarCloud docs: https://sonarcloud.io/documentation
- SonarQube docs: https://docs.sonarsource.com/sonarqube-server
