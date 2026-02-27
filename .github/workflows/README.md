# CoffeeStudio Platform CI/CD Pipeline

This repository uses GitHub Actions for a comprehensive CI/CD pipeline that ensures code quality, security, and reliable deployments.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CI/CD Pipeline                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Backend    │  │  Frontend    │  │  Security    │          │
│  │   CI Tests   │  │  CI Tests    │  │   Scans      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         └──────────┬───────┴──────────────────┘                  │
│                    │                                              │
│         ┌──────────▼──────────┐                                  │
│         │   Docker Build      │                                  │
│         │   & Push Images     │                                  │
│         └──────────┬──────────┘                                  │
│                    │                                              │
│         ┌──────────▼──────────┐                                  │
│         │  Deploy to Staging  │ (auto on develop)               │
│         └──────────┬──────────┘                                  │
│                    │                                              │
│         ┌──────────▼──────────┐                                  │
│         │ Deploy to Production│ (manual approval)               │
│         └──────────┬──────────┘                                  │
│                    │                                              │
│         ┌──────────▼──────────┐                                  │
│         │  Post-Deploy        │                                  │
│         │  Monitoring         │                                  │
│         └─────────────────────┘                                  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Workflows

### 1. **CI Pipeline** (`.github/workflows/ci.yml`)
Main orchestrator that runs all CI checks on every push and PR.

**Triggered by:**
- Push to `main`, `develop`
- Pull requests to `main`, `develop`

**Jobs:**
- Backend CI tests
- Frontend CI tests
- Security scans
- Docker builds

### 2. **Backend CI** (`.github/workflows/ci-backend.yml`)
Comprehensive backend testing pipeline.

**Features:**
- ✅ Linting (Ruff)
- ✅ Type checking (MyPy)
- ✅ Code formatting (Black/Ruff)
- ✅ Unit tests with PostgreSQL & Redis
- ✅ Code coverage (70% minimum)
- ✅ Integration tests
- ✅ API health checks

**Services:**
- PostgreSQL 16
- Redis 7

### 3. **Frontend CI** (`.github/workflows/ci-frontend.yml`)
Frontend testing and build validation.

**Features:**
- ✅ ESLint linting
- ✅ TypeScript type checking
- ✅ Unit tests (when available)
- ✅ Production build validation
- ✅ E2E tests with full Docker stack
- ✅ Build artifact upload

### 4. **Security Scans** (`.github/workflows/ci-security.yml`)
Multi-layered security scanning.

**Tools:**
- 🔒 **Bandit** - Python security scanner
- 🔒 **Trivy** - Container & filesystem vulnerability scanner
- 🔒 **Snyk** - Dependency vulnerability scanner (optional)
- 🔒 **CodeQL** - Static analysis security testing (SAST)
- 🔒 **Semgrep** - Additional SAST analysis

**Triggers:**
- Every push
- Pull requests
- Weekly schedule (Monday 2am UTC)
- Manual dispatch

### 5. **Docker Build & Push** (`.github/workflows/docker-build.yml`)
Automated container image building and publishing.

**Features:**
- 🐳 Multi-platform builds (amd64, arm64)
- 🐳 Push to GitHub Container Registry
- 🐳 Push to Docker Hub (optional)
- 🐳 Smart tagging (branch, tag, SHA, latest)
- 🐳 Build cache optimization
- 🐳 Post-push security scanning

**Image Registries:**
- `ghcr.io/<org>/<repo>/backend`
- `ghcr.io/<org>/<repo>/frontend`
- Docker Hub (if credentials configured)

### 6. **Staging Deployment** (`.github/workflows/cd-staging.yml`)
Automated deployment to staging environment.

**Triggered by:**
- Push to `develop` branch
- Manual dispatch

**Features:**
- 🚀 Automated SSH deployment
- 🚀 Database migration
- 🚀 Health checks
- 🚀 Smoke tests
- 🚀 Slack notifications (optional)
- 🚀 Deployment tracking

### 7. **Production Deployment** (`.github/workflows/cd-production.yml`)
Manual production deployment with safety features.

**Triggered by:**
- Git tags (`v*`)
- Manual dispatch with version selection

**Features:**
- 🚨 Manual approval required (GitHub environment)
- 💾 Automatic database backup
- ✅ Health checks with retries
- 🔄 Automatic rollback on failure
- 📢 Team notifications
- 📝 GitHub release notes

**Safety Features:**
- Requires environment approval
- Pre-deployment backup
- 10-attempt health check
- Auto-rollback to previous tag
- Rollback verification

### 8. **Post-Deployment Monitoring** (`.github/workflows/monitoring.yml`)
Continuous health monitoring after deployments.

**Triggered by:**
- After production deployment
- Every 30 minutes (scheduled)
- Manual dispatch

**Monitors:**
- 🏥 API health endpoint
- 🏥 Frontend accessibility
- 🏥 Database connectivity
- 🏥 Redis connectivity
- 🏥 Response time
- 🏥 SSL certificate
- 🏥 Critical API endpoints

**Alerting:**
- Creates GitHub issues on critical failures
- Sends Slack notifications
- Generates health reports

## Configuration

### Required Secrets

#### Docker Registry (Optional)
```bash
DOCKER_USERNAME       # Docker Hub username
DOCKER_PASSWORD       # Docker Hub password or access token
```

#### Code Coverage (Optional)
```bash
CODECOV_TOKEN        # Codecov.io token for coverage reports
```

#### Staging Deployment (Optional)
```bash
STAGING_SSH_KEY      # SSH private key for staging server
STAGING_HOST         # Staging server hostname
STAGING_USER         # SSH user for staging deployment
```

#### Production Deployment (Optional)
```bash
PRODUCTION_SSH_KEY   # SSH private key for production server
PRODUCTION_HOST      # Production server hostname
PRODUCTION_USER      # SSH user for production deployment
```

#### Notifications (Optional)
```bash
SLACK_WEBHOOK        # Slack webhook URL for notifications
```

#### Security Scanning (Optional)
```bash
SNYK_TOKEN          # Snyk API token for dependency scanning
```

### GitHub Environment Configuration

**Staging Environment:**
- Name: `staging`
- URL: `https://staging.coffeestudio.example.com`
- Protection rules: None (auto-deploy)

**Production Environment:**
- Name: `production`
- URL: `https://coffeestudio.example.com`
- Protection rules: 
  - ✅ Required reviewers (recommended: 1-2 people)
  - ✅ Wait timer (optional: 5-10 minutes)

## Branch Strategy

```
main (production)
  ↑
  └─ v1.0.0, v1.1.0, ... (tags)

develop (staging)
  ↑
  └─ feature/*, fix/*, ...
```

**Workflow:**
1. Create feature branch from `develop`
2. Open PR to `develop` → CI runs
3. Merge to `develop` → Auto-deploy to staging
4. Test in staging
5. Create PR from `develop` to `main`
6. Merge to `main` → Create tag
7. Tag push → Manual deploy to production

## Local Testing

### Backend
```bash
cd apps/api
pip install -r requirements.txt -r requirements-dev.txt
ruff check app/ tests/
mypy --config-file ../mypy.ini app/
pytest tests/ --cov=app
```

### Frontend
```bash
cd apps/web
npm ci
npm run lint
npx tsc --noEmit
npm test
npm run build
```

### Docker
```bash
# Build images
docker build -t coffeestudio-backend:test apps/api/
docker build -t coffeestudio-frontend:test apps/web/

# Run full stack
docker compose up -d
```

### Security Scans
```bash
# Bandit
pip install bandit[toml]
bandit -r apps/api/app/

# Trivy
trivy fs .
trivy image coffeestudio-backend:test
```

## Pipeline Performance

**Expected Execution Times:**
- Backend CI: ~3-5 minutes
- Frontend CI: ~5-7 minutes
- Security Scans: ~5-10 minutes
- Docker Build: ~8-12 minutes
- **Total CI Time: ~12-15 minutes** (parallel execution)

**Deployment Times:**
- Staging: ~2-3 minutes
- Production: ~3-5 minutes (including health checks)

## Troubleshooting

### CI Failures

**Backend tests failing:**
```bash
# Check logs in GitHub Actions
# Common issues:
- Missing database migrations
- Environment variable issues
- Dependency conflicts
```

**Frontend build failing:**
```bash
# Check Node.js version (should be 20)
# Check for TypeScript errors
# Verify all dependencies are in package.json
```

**Security scan failures:**
- Review SARIF reports in Security tab
- Fix high/critical vulnerabilities
- Update dependencies if needed

### Deployment Issues

**Staging deployment failing:**
- Verify SSH key is correct
- Check server accessibility
- Review server logs
- Verify Docker Compose setup

**Production rollback:**
- Automatic rollback triggers on health check failure
- Manual rollback: SSH to server, `git checkout <previous-tag>`, `docker compose up -d`

## Monitoring

### GitHub Actions
- View workflow runs: `Actions` tab
- Download artifacts: Build reports, coverage, security scans
- Review logs: Detailed execution logs

### Security Tab
- View security alerts
- Review CodeQL findings
- Check Trivy scan results

### Deployments
- View deployment history: `Environments` in repo settings
- Check deployment status
- Review health check reports

## Best Practices

1. **Always run CI locally before pushing**
2. **Review security scan results**
3. **Test in staging before production**
4. **Monitor production after deployment**
5. **Keep dependencies updated**
6. **Use semantic versioning for releases**
7. **Document breaking changes in PR descriptions**
8. **Set up branch protection rules**

## Status Badge

Add to your README.md:

```markdown
[![CI Pipeline](https://github.com/<org>/<repo>/workflows/CI%20Pipeline/badge.svg)](https://github.com/<org>/<repo>/actions/workflows/ci.yml)
```

## Metrics

Track these metrics to measure pipeline effectiveness:

- ✅ **Build Success Rate**: Target > 95%
- ✅ **Test Coverage**: Target > 80%
- ✅ **Deployment Frequency**: Daily to staging, weekly to production
- ✅ **Mean Time to Recovery (MTTR)**: < 30 minutes
- ✅ **Security Vulnerabilities**: Zero critical/high

## Future Enhancements

- [ ] Add performance testing (k6, Lighthouse)
- [ ] Implement blue-green deployments
- [ ] Add canary deployments
- [ ] Integrate with PagerDuty/Opsgenie
- [ ] Add deployment approval webhooks
- [ ] Implement automatic dependency updates (Dependabot)

## Support

For issues with the CI/CD pipeline:
1. Check workflow logs in GitHub Actions
2. Review this documentation
3. Open an issue with label `ci-cd`
4. Contact DevOps team

---

**Last Updated:** 2024-12-30  
**Version:** 1.0.0
