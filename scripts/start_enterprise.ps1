<#
Start the enterprise Docker Compose stack and run basic health checks.

Usage:
  .\scripts\start_enterprise.ps1

This script performs lightweight checks and then runs:
  docker compose -f infra/deploy/docker-compose.enterprise.yml up --build -d

It requires Docker and Docker Compose available in PATH.
#>

param(
    [ValidateSet('start','stop','logs','status','restart','help')
$ErrorActionPreference = 'Stop'


function Assert-DockerEngine {
    try {
        $null = docker version --format "{{.Server.Version}}" 2>$null
    } catch {
        Write-Error "Docker CLI is installed but the Docker engine is not reachable.

Fix:
- Start Docker Desktop
- Ensure it is set to Linux containers (WSL2 backend)
- Then re-run this script.

Diagnostic commands:
  docker context ls
  docker context show
  docker version
"
        exit 10
    }
}

]
    [string]$action = 'start',
    [string]$composeFile = 'infra/deploy/docker-compose.enterprise.yml',
    [string]$envExample = 'infra/env/enterprise.env.example',
    [string]$envFile = 'infra/env/enterprise.env',
    [string]$healthUrl = 'http://localhost:8000/health',
    [int]$timeoutSec = 120,
    [switch]$FollowLogs
)

function Ensure-Command($name, $installUrl) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Error "$name not found. Install from: $installUrl"
        exit 2
    }
}

Ensure-Command -name 'docker' -installUrl 'https://www.docker.com/'
Assert-DockerEngine

if (-not (Test-Path $composeFile)) {
    Write-Error "Compose file not found: $composeFile"
    exit 3
}

if (-not (Test-Path $envFile)) {
    New-Item -ItemType Directory -Path (Split-Path $envFile) -Force | Out-Null
    if (Test-Path $envExample) {
        Write-Host "Copying $envExample -> $envFile"
        Copy-Item $envExample $envFile -Force
    } else {
        Write-Warning "No $envFile or $envExample found. Creating safe placeholder $envFile (no secrets)."
        @'
# Enterprise environment (auto-generated placeholder)
DATABASE_URL=postgresql+psycopg://coffeestudio:changeme@postgres:5432/coffeestudio
REDIS_URL=redis://redis:6379/0
JWT_SECRET=replace-with-a-secure-secret-of-at-least-32-chars
CORS_ORIGINS=http://localhost:3000
PERPLEXITY_API_KEY=
'@ | Set-Content -Path $envFile -Encoding UTF8
    }
}

function Show-Help {
    Write-Host "Usage: .\scripts\start_enterprise.ps1 [-action start|stop|logs|status|restart|help] [-FollowLogs]"
    Write-Host "Examples:"
    Write-Host "  .\scripts\start_enterprise.ps1 -action start"
    Write-Host "  .\scripts\start_enterprise.ps1 -action start -FollowLogs"
    Write-Host "  .\scripts\start_enterprise.ps1 -action logs"
    Write-Host "  .\scripts\start_enterprise.ps1 -action stop"
}

switch ($action) {
    'help' {
        Show-Help; exit 0
    }
    'start' {
        Write-Host "Starting enterprise stack using $composeFile..."
        docker compose -f $composeFile up --build -d

        Write-Host 'Waiting for health endpoint:' $healthUrl
        $deadline = (Get-Date).AddSeconds($timeoutSec)
        while ((Get-Date) -lt $deadline) {
            try {
                $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
                if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300) {
                    Write-Host "Health check OK: $($r.StatusCode)"
                    break
                }
            } catch {
                Write-Host -NoNewline '.'
                Start-Sleep -Seconds 2
            }
        }

        if ((Get-Date) -ge $deadline) {
            Write-Warning "Health check did not succeed within $timeoutSec seconds. Check container logs: docker compose -f $composeFile logs -f"
        } else {
            Write-Host 'Enterprise stack started and responding.'
            Write-Host 'Run smoke tests:'
            Write-Host "  pytest -q apps/api/tests -k smoke"
        }

        if ($FollowLogs) {
            Write-Host "Following logs (ctrl-c to stop):"
            docker compose -f $composeFile logs -f
        }
    }
    'stop' {
        Write-Host "Stopping and removing enterprise stack (volumes)..."
        docker compose -f $composeFile down -v
    }
    'logs' {
        Write-Host "Streaming logs for $composeFile (ctrl-c to stop)..."
        docker compose -f $composeFile logs -f
    }
    'status' {
        Write-Host "Container status for $composeFile"
        docker compose -f $composeFile ps
    }
    'restart' {
        Write-Host "Restarting enterprise stack..."
        docker compose -f $composeFile down -v
        docker compose -f $composeFile up --build -d
        if ($FollowLogs) { docker compose -f $composeFile logs -f }
    }
    default { Show-Help }
}

