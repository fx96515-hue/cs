# Branch Protection / Ruleset (Empfehlung)

## Zielbranch: `main`
Aktiviere in GitHub (Settings -> Branches / Rulesets):

- **Require a pull request before merging** ✅
- **Require approvals** (mind. 1) ✅
- **Dismiss stale approvals when new commits are pushed** ✅
- **Require status checks to pass before merging** ✅
- **Require branches to be up to date before merging** ✅
- **Require conversation resolution before merging** ✅
- **Restrict direct pushes to matching branches** ✅
- **Allow force pushes** ❌
- **Allow deletions** ❌
- **Allow auto-merge** ✅ (optional, empfohlen wenn CI stabil)
- **Require linear history** optional (wenn Squash-Only)

## Required Status Checks (Beispiele)
Nutze die tatsächlichen Workflow-Namen aus eurem Repo, z. B.:
- Backend CI
- Frontend CI
- CI Pipeline
- Security / Code Scanning
- Docker Build (falls PR-relevant)

## Merge-Strategie
Empfohlen:
- **Squash merge** ✅
Nicht empfohlen:
- Direktes Mergen in `main`
