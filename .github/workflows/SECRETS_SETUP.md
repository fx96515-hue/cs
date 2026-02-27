# CI/CD Secrets Setup Guide

This guide explains how to configure the required secrets for the CI/CD pipeline.

## Quick Start

The pipeline works without any secrets configured, but with limited functionality:
- ✅ All CI tests will run
- ✅ Security scans will run (except Snyk)
- ✅ Docker images will be built
- ⚠️ Docker images won't be pushed (no registry credentials)
- ⚠️ Deployments won't execute (no SSH credentials)
- ⚠️ No Slack notifications (no webhook)

## Setting Up Secrets

Go to: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

### 1. Docker Registry (Optional but Recommended)

Push Docker images to registries for deployment.

#### Option A: GitHub Container Registry (GHCR) - Free
Already configured! Uses `GITHUB_TOKEN` automatically. No setup needed.

Images will be pushed to:
- `ghcr.io/<org>/<repo>/backend:<tag>`
- `ghcr.io/<org>/<repo>/frontend:<tag>`

#### Option B: Docker Hub - Additional Registry
```
DOCKER_USERNAME      # Your Docker Hub username
DOCKER_PASSWORD      # Docker Hub personal access token (not password!)
```

**How to create Docker Hub token:**
1. Go to https://hub.docker.com/settings/security
2. Click "New Access Token"
3. Name: "GitHub Actions CI/CD"
4. Permissions: "Read, Write, Delete"
5. Copy the token and save as `DOCKER_PASSWORD` secret

### 2. Code Coverage (Optional)

Get coverage reports on pull requests.

```
CODECOV_TOKEN       # Get from https://codecov.io
```

**Setup:**
1. Go to https://codecov.io
2. Sign up with GitHub
3. Add your repository
4. Copy the upload token
5. Save as `CODECOV_TOKEN` secret

### 3. Staging Deployment (Required for Auto-Deploy)

Enable automatic deployments to staging environment.

```
STAGING_SSH_KEY     # SSH private key for staging server
STAGING_HOST        # Staging server hostname (e.g., staging.example.com)
STAGING_USER        # SSH username (e.g., deploy)
```

**How to create SSH key:**
```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions-staging" -f staging_key -N ""

# Copy private key content (save as STAGING_SSH_KEY)
cat staging_key

# Copy public key to server
ssh-copy-id -i staging_key.pub user@staging.example.com

# Or manually add to server's ~/.ssh/authorized_keys
cat staging_key.pub
```

**Server Setup:**
```bash
# On staging server
sudo mkdir -p /opt/coffeestudio
sudo chown $USER:$USER /opt/coffeestudio
cd /opt/coffeestudio
git clone https://github.com/<org>/<repo>.git .
git checkout develop

# Install Docker & Docker Compose
# See: https://docs.docker.com/engine/install/

# Create .env file with required variables
cp .env.example .env
# Edit .env with production values
```

### 4. Production Deployment (Required for Prod Deploy)

Enable deployments to production environment.

```
PRODUCTION_SSH_KEY  # SSH private key for production server
PRODUCTION_HOST     # Production server hostname (e.g., example.com)
PRODUCTION_USER     # SSH username (e.g., deploy)
```

**Setup:** Same as staging, but with separate key and server.

**⚠️ Important Security Notes:**
- Use different SSH keys for staging and production
- Use dedicated deploy user with minimal permissions
- Consider using `NOPASSWD` sudo for specific docker commands only
- Enable firewall (UFW) on servers
- Keep SSH private keys secure - never commit them

### 5. Notifications (Optional)

Get deployment notifications in Slack.

```
SLACK_WEBHOOK       # Slack incoming webhook URL
```

**How to create Slack webhook:**
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "CoffeeStudio CI/CD"
4. Select your workspace
5. Click "Incoming Webhooks"
6. Toggle "Activate Incoming Webhooks" to On
7. Click "Add New Webhook to Workspace"
8. Select channel (e.g., #deployments)
9. Copy webhook URL
10. Save as `SLACK_WEBHOOK` secret

### 6. Security Scanning (Optional)

Enable Snyk dependency scanning.

```
SNYK_TOKEN          # Snyk API token
```

**Setup:**
1. Go to https://snyk.io
2. Sign up with GitHub
3. Go to Account Settings → API Token
4. Copy the token
5. Save as `SNYK_TOKEN` secret

## GitHub Environments Setup

For production deployments with manual approval:

1. Go to **Settings** → **Environments**
2. Click "New environment"
3. Name: `production`
4. Enable "Required reviewers"
5. Add 1-2 reviewers
6. (Optional) Add "Wait timer" (e.g., 5 minutes)
7. Save

For staging:
1. Create environment named `staging`
2. No protection rules needed (auto-deploy)
3. (Optional) Set environment URL: `https://staging.coffeestudio.example.com`

## Verification

After setting up secrets, verify with:

```bash
# Check secrets are set (won't show values)
gh secret list

# Trigger a test workflow
git commit --allow-empty -m "Test CI/CD pipeline"
git push
```

## Secret Summary by Feature

| Feature | Required Secrets | Status if Missing |
|---------|-----------------|-------------------|
| CI Tests | None | ✅ Fully functional |
| Security Scans | None (SNYK_TOKEN optional) | ✅ Mostly functional |
| Docker Build | None | ✅ Builds but doesn't push |
| GHCR Push | None (uses GITHUB_TOKEN) | ✅ Fully functional |
| Docker Hub Push | DOCKER_USERNAME, DOCKER_PASSWORD | ⚠️ Skipped |
| Coverage Reports | CODECOV_TOKEN | ⚠️ No reports |
| Staging Deploy | STAGING_* (3 secrets) | ⚠️ Placeholder only |
| Production Deploy | PRODUCTION_* (3 secrets) | ⚠️ Placeholder only |
| Slack Notifications | SLACK_WEBHOOK | ⚠️ No notifications |

## Security Best Practices

1. **Rotate secrets regularly** (every 90 days)
2. **Use different keys** for staging and production
3. **Limit SSH key permissions** (read-only except deploy dir)
4. **Enable branch protection** on main branch
5. **Require status checks** to pass before merge
6. **Use environment protection** for production
7. **Audit secret access** in Settings → Logs
8. **Never commit secrets** to repository

## Troubleshooting

### "Error: The workflow is not valid"
- **Cause**: GitHub Actions syntax error when checking secrets in `if` conditions
- **Solution**: Always wrap secret checks in `${{ }}` expression syntax
- **Example**: Use `if: ${{ secrets.MY_SECRET != '' }}` instead of `if: secrets.MY_SECRET != ''`
- Note: This is a known GitHub Actions limitation where secrets cannot be directly referenced in conditional expressions

### "Error: secret not found"
- Check secret name matches exactly (case-sensitive)
- Verify secret is set in repository settings

### "Permission denied (publickey)"
- Verify SSH key is correct format (include `-----BEGIN/END-----`)
- Ensure public key is on server in `~/.ssh/authorized_keys`
- Check SSH user has permissions to `/opt/coffeestudio`

### "Docker login failed"
- For Docker Hub: Use personal access token, not password
- For GHCR: Token is automatic, check package permissions

### Deployments not running
- Check if environment exists (Settings → Environments)
- Verify SSH secrets are configured
- Check workflow logs for specific errors

## Support

For help with CI/CD setup:
1. Check `.github/workflows/README.md` for pipeline docs
2. Review GitHub Actions logs
3. Open issue with label `ci-cd`

---

**Last Updated:** 2024-12-30  
**Version:** 1.0.0
