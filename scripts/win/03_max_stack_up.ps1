<#
CoffeeStudio MAX stack bootstrap (Windows).

- Runs the full "stack" profile (Traefik + Ops + Observability + LLM + Workflows)
- Creates an automatic ZIP backup after every step
- Runs diagnostics + guided troubleshooting on failures

Usage:
  .\scripts\win\03_max_stack_up.ps1

Tips:
- If you hit disk-full during backup: set COFFEESTUDIO_BACKUP_TMP to another drive, e.g. D:\Temp
- If Docker is acting weird (500 / pipe / API version): Run .\scripts\win\99_diagnose_docker.ps1
#>

$ErrorActionPreference = "Stop"

function New-Timestamp() { (Get-Date).ToString("yyyyMMdd_HHmmss") }

function Ensure-Dir($path) {
  if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path | Out-Null }
}

function Backup-Project([string]$label) {
  Ensure-Dir ".\backups"
  $ts  = New-Timestamp
  $zip = ".\backups\coffeestudio_${ts}_${label}.zip"

  # Use alternate temp root if provided (fixes "disk full" on C:)
  $tmpRoot = $env:COFFEESTUDIO_BACKUP_TMP
  if (-not $tmpRoot) { $tmpRoot = $env:TEMP }
  $tmp = Join-Path $tmpRoot ("coffeestudio_backup_" + $ts)

  if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
  New-Item -ItemType Directory -Path $tmp | Out-Null

  # Exclude bulky / recursive directories (keeps backups small + fast)
  $exclude = @(
    "backups","diagnostics",".git",
    "node_modules",".venv","__pycache__",
    ".mypy_cache",".pytest_cache",".ruff_cache",
    "data","volumes","out","dist","build"
  )

  $items = Get-ChildItem -Force -Path . | Where-Object { $_.Name -notin $exclude }
  foreach ($i in $items) {
    Copy-Item -Recurse -Force -Path $i.FullName -Destination (Join-Path $tmp $i.Name)
  }

  if (Test-Path $zip) { Remove-Item -Force $zip }
  Compress-Archive -Path (Join-Path $tmp "*") -DestinationPath $zip -Force
  Remove-Item -Recurse -Force $tmp

  Write-Host "Backup: $zip" -ForegroundColor DarkGreen
}

function Assert-Command($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "Missing command: $name"
  }
}

function Invoke-Docker([scriptblock]$cmd, [int]$retries = 12, [int]$sleepSec = 5) {
  # Retries docker/compose commands across transient Docker Desktop pipe restarts.
  for ($i=1; $i -le $retries; $i++) {
    try {
      return (& $cmd)
    } catch {
      $m = $_.Exception.Message
      $isTransient = ($m -match "dockerDesktopLinuxEngine" -or $m -match "dockerDesktopWindowsEngine" -or $m -match "The system cannot find the file specified" -or $m -match "underlying connection was closed" -or $m -match "unterwartet getrennt" -or $m -match "unexpectedly terminated" -or $m -match "Internal Server Error")
      if (-not $isTransient -or $i -eq $retries) { throw }
      Write-Host ("Docker API not ready (try $i/$retries): " + $m) -ForegroundColor Yellow
      Start-Sleep -Seconds $sleepSec
    }
  }
}

function Diagnose-Docker([string]$hint) {
  Ensure-Dir ".\diagnostics"
  $ts = New-Timestamp
  $outDir = ".\diagnostics\diag_${ts}"
  Ensure-Dir $outDir

  $cmds = @(
    @{n="docker_version.txt"; c={ docker version | Out-String }},
    @{n="docker_info.txt"; c={ docker info 2>&1 | Out-String }},
    @{n="docker_context_ls.txt"; c={ docker context ls 2>&1 | Out-String }},
    @{n="compose_version.txt"; c={ docker compose version 2>&1 | Out-String }},
    @{n="compose_config.txt"; c={ docker compose -f docker-compose.yml -f docker-compose.stack.yml config 2>&1 | Out-String }},
    @{n="compose_ps.txt"; c={ docker compose -f docker-compose.yml -f docker-compose.stack.yml ps 2>&1 | Out-String }},
    @{n="compose_logs_backend.txt"; c={ docker compose -f docker-compose.yml -f docker-compose.stack.yml logs --tail 200 backend 2>&1 | Out-String }},
    @{n="compose_logs_traefik.txt"; c={ docker compose -f docker-compose.yml -f docker-compose.stack.yml logs --tail 200 traefik 2>&1 | Out-String }}
  )

  foreach ($x in $cmds) {
    try {
      & $x.c | Set-Content -Path (Join-Path $outDir $x.n) -Encoding UTF8
    } catch {
      ("ERROR collecting " + $x.n + ": " + $_.Exception.Message) | Set-Content -Path (Join-Path $outDir $x.n) -Encoding UTF8
    }
  }

  if ($hint) { $hint | Set-Content -Path (Join-Path $outDir "HINT.txt") -Encoding UTF8 }

  Write-Host "Diagnostics written: $outDir" -ForegroundColor Yellow
}

function Guided-Troubleshooting([string]$err) {
  Write-Host "`n=== Guided Troubleshooting ===" -ForegroundColor Yellow
  Write-Host $err -ForegroundColor Red

  if ($err -match "dockerDesktopLinuxEngine" -or $err -match "dockerDesktopWindowsEngine" -or $err -match "check if the server supports the requested API version" -or $err -match "Internal Server Error" -or $err -match "unterwartet getrennt") {
    Write-Host "`nLikely: Docker Desktop engine/context is restarting or unstable (often low RAM)." -ForegroundColor Yellow
    Write-Host "Try (in this order):" -ForegroundColor Yellow
    Write-Host "  1) Ensure context = desktop-linux (docker context use desktop-linux)" -ForegroundColor Yellow
    Write-Host "  2) Restart Docker Desktop and wait until 'Engine running'" -ForegroundColor Yellow
    Write-Host "  3) wsl --shutdown  (then restart Docker Desktop)" -ForegroundColor Yellow
    Write-Host "  4) Increase Docker Desktop Resources (Memory) to 8GB+ for MAX stack" -ForegroundColor Yellow
  }

  Write-Host "`nCollecting diagnostics..." -ForegroundColor Yellow
  Diagnose-Docker -hint $err
  Write-Host "==============================`n" -ForegroundColor Yellow
}

function Wait-BackendHealthy([int]$timeoutSec = 300) {
  $deadline = (Get-Date).AddSeconds($timeoutSec)
  while ((Get-Date) -lt $deadline) {
    try {
      $cid = (Invoke-Docker { docker compose -f docker-compose.yml -f docker-compose.stack.yml ps -q backend } 6 4) | Select-Object -First 1
      if ($cid) {
        $st = Invoke-Docker { docker inspect -f "{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}" $cid } 6 4
        if ($st -match "running\|healthy") { return $true }
        if ($st -match "running\|unhealthy") { return $false }
      }
    } catch { }
    Start-Sleep -Seconds 4
  }
  return $false
}

function Try-Http([string]$url, [int]$timeoutSec = 10) {
  try {
    $h = Invoke-RestMethod -Uri $url -TimeoutSec $timeoutSec
    return @{ ok=$true; data=$h }
  } catch {
    return @{ ok=$false; err=$_.Exception.Message }
  }
}

# ---- MAIN ----
Assert-Command docker

Set-Location -Path $PSScriptRoot
Set-Location -Path "..\.."   # repo root (coffeestudio-platform)

Write-Host "== CoffeeStudio MAX STACK ==" -ForegroundColor Cyan

Backup-Project "step00_before"

# Ensure .env
if (-not (Test-Path ".env")) {
  Copy-Item .env.example .env
  Write-Host "Created .env from .env.example" -ForegroundColor Green
}
Backup-Project "step01_env"

# Ensure stack profile
$env:COMPOSE_PROFILES = "stack"

# Preflight (with retries across engine restarts)
try {
  Invoke-Docker { docker info | Out-Null } 12 5
  Invoke-Docker { docker compose version | Out-Null } 12 5
} catch {
  Guided-Troubleshooting $_.Exception.Message
  throw
}
Backup-Project "step02_preflight"

# Pull (non-fatal)
try {
  Invoke-Docker { docker compose -f docker-compose.yml -f docker-compose.stack.yml pull } 6 5 | Out-Null
} catch {
  Write-Host "Pull failed (continuing). Details: $($_.Exception.Message)" -ForegroundColor Yellow
}
Backup-Project "step03_pull"

# Up
try {
  Invoke-Docker { docker compose -f docker-compose.yml -f docker-compose.stack.yml up -d --build } 6 6 | Out-Null
} catch {
  Guided-Troubleshooting $_.Exception.Message
  throw
}
Backup-Project "step04_up"

# Health checks
Write-Host "Health checks..." -ForegroundColor Cyan

# 1) Wait for backend container health (don't hit Traefik too early)
$ok = Wait-BackendHealthy 300
if (-not $ok) {
  Write-Host "Backend did not become healthy in time (or turned unhealthy). Showing last backend logs:" -ForegroundColor Red
  try { Invoke-Docker { docker compose -f docker-compose.yml -f docker-compose.stack.yml logs --tail 250 backend } 6 5 | Out-Host } catch { }
  Guided-Troubleshooting "Backend health failed. Check backend logs (alembic/DB/curl healthcheck) and Docker Desktop resources."
  throw "Backend unhealthy / not ready."
}

# 2) Check direct port (bypasses Traefik)
$r1 = Try-Http "http://localhost:8000/health" 10
if ($r1.ok) {
  Write-Host ("API health (direct): " + ($r1.data | ConvertTo-Json -Compress)) -ForegroundColor Green
} else {
  Write-Host ("Direct API health failed: " + $r1.err) -ForegroundColor Yellow
}

# 3) Check via Traefik host route
$r2 = Try-Http "http://api.localhost/health" 10
if ($r2.ok) {
  Write-Host ("API health (traefik): " + ($r2.data | ConvertTo-Json -Compress)) -ForegroundColor Green
} else {
  Write-Host ("Traefik API health failed (can be DNS/hosts/localhost routing): " + $r2.err) -ForegroundColor Yellow
  Write-Host "Tip: open http://traefik.localhost/dashboard/ and confirm router 'api@docker' exists." -ForegroundColor Yellow
}

Backup-Project "step05_health"

Write-Host "`nOPEN:" -ForegroundColor Green
Write-Host "  UI:        http://ui.localhost" -ForegroundColor Green
Write-Host "  API:       http://api.localhost/docs  (direct: http://localhost:8000/docs)" -ForegroundColor Green
Write-Host "  Traefik:   http://traefik.localhost/dashboard/" -ForegroundColor Green
Write-Host "  Portainer: http://docker.localhost" -ForegroundColor Green
Write-Host "  Grafana:   http://ops.localhost  (admin/adminadmin)" -ForegroundColor Green
Write-Host "  Prom:      http://prom.localhost" -ForegroundColor Green
Write-Host "  n8n:       http://flows.localhost" -ForegroundColor Green
Write-Host "  LLM UI:    http://llm.localhost" -ForegroundColor Green
Write-Host "  LiteLLM:   http://llm-api.localhost" -ForegroundColor Green
Write-Host "  Langfuse:  http://langfuse.localhost" -ForegroundColor Green
Write-Host "  WUD:       http://wud.localhost" -ForegroundColor Green
