# SonarQube / SonarCloud Integration

This document explains the minimal SonarCloud integration scaffold added to the repository.

What was added
- `.github/workflows/sonarcloud.yml` — GitHub Actions workflow that runs SonarCloud analysis on push/PR.
- `sonar.projectKey` and `sonar.organization` are configured in the workflow. You must update these values for your SonarCloud organization if different.

Requirements
- Create a repository secret `SONAR_TOKEN` with a SonarCloud token (or SonarQube token if using self-hosted scanner).
- If you use SonarCloud, register the project under your organization and update `sonar.projectKey`.

How it works
- The workflow installs Python dependencies and runs the SonarCloud GitHub Action.
- The action uploads analysis results to SonarCloud where you can see security hotspots, code smells, and metric trends.

Local testing
- You can run `sonar-scanner` locally against the codebase if you have SonarQube installed.

More
- SonarCloud docs: https://sonarcloud.io/documentation
- Self-hosted SonarQube: https://docs.sonarqube.org
