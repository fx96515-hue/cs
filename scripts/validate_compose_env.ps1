<#
Validates presence of the env file expected by the enterprise compose.

Enterprise compose (default):
  infra/deploy/docker-compose.enterprise.yml

Expected env files:
  infra/env/enterprise.env.example (tracked example)
  infra/env/enterprise.env        (local, not committed)

This script NEVER copies secrets into the example file.
If the example is missing, it creates a SAFE placeholder example, then ensures
the local `enterprise.env` exists (copied from the example).

Usage:
  .\scripts\validate_compose_env.ps1
#>

$ErrorActionPreference = 'Stop'

$repoRoot = (Get-Location).Path
$expectedExample = Join-Path $repoRoot 'infra\env\enterprise.env.example'
$expectedEnv = Join-Path $repoRoot 'infra\env\enterprise.env'

if (-not (Test-Path $expectedExample)) {
    Write-Warning "Enterprise env example missing: $expectedExample"
    Write-Host "Creating a safe placeholder enterprise.env.example (no secrets)..."
    New-Item -ItemType Directory -Path (Split-Path $expectedExample) -Force | Out-Null

    @'
# Enterprise environment example (auto-generated placeholder)
DATABASE_URL=postgresql+psycopg://coffeestudio:changeme@postgres:5432/coffeestudio
REDIS_URL=redis://redis:6379/0
JWT_SECRET=replace-with-a-secure-secret-of-at-least-32-chars
CORS_ORIGINS=http://localhost:3000
PERPLEXITY_API_KEY=
'@ | Set-Content -Path $expectedExample -Encoding UTF8

    Write-Host "Created: $expectedExample"
} else {
    Write-Host "Found enterprise env example: $expectedExample"
}

if (-not (Test-Path $expectedEnv)) {
    Write-Warning "Enterprise env missing: $expectedEnv"
    Write-Host "Creating $expectedEnv from example (no secrets by default)..."
    New-Item -ItemType Directory -Path (Split-Path $expectedEnv) -Force | Out-Null
    Copy-Item $expectedExample $expectedEnv -Force
    Write-Host "Created: $expectedEnv"
} else {
    Write-Host "Found enterprise env: $expectedEnv"
}

exit 0
