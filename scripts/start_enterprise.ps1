<#
Start the enterprise Docker Compose stack and run basic health checks.

Usage:
  .\scripts\start_enterprise.ps1 -action start -FollowLogs
#>

[CmdletBinding()]
param(
  [ValidateSet('start','stop','restart','status','logs','help')]
  [string]$action = 'start',

  [string]$composeFile = 'infra/deploy/docker-compose.enterprise.yml',
  [string]$envExample  = 'infra/env/enterprise.env.example',
  [string]$envFile     = 'infra/env/enterprise.env',
  [string]$healthUrl   = 'http://localhost:8000/health',
  [int]$timeoutSec     = 120,
  [switch]$FollowLogs
)

$ErrorActionPreference = 'Stop'

function Ensure-Command([string]$name, [string]$installUrl) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "$name not found. Install from: $installUrl"
  }
}

function Assert-DockerEngine {
  try {
    $null = docker version --format "{{.Server.Version}}" 2>$null
  } catch {
    throw @"
Docker CLI is installed but the Docker engine is not reachable.

Fix:
- Start Docker Desktop
- Ensure it is set to Linux containers (WSL2 backend)
- Then re-run this script.

Diagnostics:
  docker context ls
  docker context show
  docker version
"@
  }
}

function Ensure-EnvFile {
  if (Test-Path $envFile) { return }

  New-Item -ItemType Directory -Path (Split-Path $envFile) -Force | Out-Null

  if (Test-Path $envExample) {
    Write-Host "Copying $envExample -> $envFile"
    Copy-Item $envExample $envFile -Force
    return
  }

  Write-Warning "No $envFile or $envExample found. Creating safe placeholder $envFile (no secrets)."
@"
# Enterprise environment (auto-generated placeholder)
DATABASE_URL=postgresql+psycopg://coffeestudio:changeme@postgres:5432/coffeestudio
REDIS_URL=redis://redis:6379/0
JWT_SECRET=replace-with-a-secure-secret-of-at-least-32-chars
CORS_ORIGINS=http://localhost:3000
PERPLEXITY_API_KEY=
"@ | Set-Content -Path $envFile -Encoding UTF8
}

function Wait-Health {
  Write-Host "Waiting for health endpoint: $healthUrl"
  $deadline = (Get-Date).AddSeconds($timeoutSec)

  while ((Get-Date) -lt $deadline) {
    try {
      $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
      if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300) {
        Write-Host "Health check OK: $($r.StatusCode)"
        return $true
      }
    } catch {
      Write-Host -NoNewline '.'
      Start-Sleep -Seconds 2
    }
  }

  Write-Host ""
  return $false
}

function Show-Help {
  Write-Host "Usage: .\scripts\start_enterprise.ps1 [-action start|stop|logs|status|restart|help] [-FollowLogs]"
  Write-Host "Examples:"
  Write-Host "  .\scripts\start_enterprise.ps1 -action start"
  Write-Host "  .\scripts\start_enterprise.ps1 -action start -FollowLogs"
  Write-Host "  .\scripts\start_enterprise.ps1 -action logs"
  Write-Host "  .\scripts\start_enterprise.ps1 -action stop"
}

Ensure-Command -name 'docker' -installUrl 'https://www.docker.com/'
Assert-DockerEngine

if (-not (Test-Path $composeFile)) { throw "Compose file not found: $composeFile" }

Ensure-EnvFile

switch ($action) {
  'help'   { Show-Help; exit 0 }
  'start'  {
    Write-Host "Starting enterprise stack using $composeFile..."
    docker compose -f $composeFile up --build -d
    if ($LASTEXITCODE -ne 0) { throw "docker compose up failed (exit $LASTEXITCODE)" }

    $ok = Wait-Health
    if (-not $ok) {
      Write-Warning "Health check did not succeed within $timeoutSec seconds. Check logs:"
      Write-Host "  docker compose -f $composeFile logs -f"
      exit 1
    }

    Write-Host "Enterprise stack started and responding."
    if ($FollowLogs) { docker compose -f $composeFile logs -f }
  }
  'stop'   { docker compose -f $composeFile down -v }
  'logs'   { docker compose -f $composeFile logs -f }
  'status' { docker compose -f $composeFile ps }
  'restart'{
    docker compose -f $composeFile down -v
    docker compose -f $composeFile up --build -d
    if ($FollowLogs) { docker compose -f $composeFile logs -f }
  }
  default  { Show-Help }
}
