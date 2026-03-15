# CoffeeStudio Option D — Windows runner (PowerShell)
# Usage: Right-click -> "Run with PowerShell" or execute: .\run_windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "== CoffeeStudio: Windows Run ==" -ForegroundColor Cyan

# Ensure we are in the script directory
Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".env")) {
  Write-Host "No .env found. Creating from .env.example ..." -ForegroundColor Yellow
  Copy-Item .env.example .env
}

# --- ensure minimal sane dev defaults (no secrets are embedded in the release) ---
function Set-EnvValue {
  param(
    [Parameter(Mandatory=$true)][string]$Key,
    [Parameter(Mandatory=$true)][string]$Value
  )
  $p = Join-Path $PSScriptRoot ".env"
  $lines = Get-Content $p
  $re = "^$([regex]::Escape($Key))=.*$"
  if ($lines -match $re) {
    $lines = $lines -replace $re, ("$Key=$Value")
  } else {
    $lines += "$Key=$Value"
  }
  Set-Content -Path $p -Value $lines -Encoding UTF8
}

function Get-EnvValue {
  param([Parameter(Mandatory=$true)][string]$Key)
  $p = Join-Path $PSScriptRoot ".env"
  if (-not (Test-Path $p)) { return $null }
  $line = (Get-Content $p | Where-Object { $_ -match "^$([regex]::Escape($Key))=" } | Select-Object -First 1)
  if (-not $line) { return $null }
  return ($line -split "=",2)[1]
}

function New-RandomSecret {
  param([int]$ByteCount = 24)
  $bytes = New-Object byte[] $ByteCount
  [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
  $raw = [Convert]::ToBase64String($bytes)
  $normalized = ($raw -replace "[^A-Za-z0-9]", "") + "Aa1!"
  return $normalized.Substring(0, [Math]::Min($normalized.Length, 28))
}

$jwt = Get-EnvValue "JWT_SECRET"
if (-not $jwt -or $jwt -eq "dev-secret-CHANGE-ME-2026-EXTRA-LENGTH" -or $jwt.Length -lt 32) {
  # Generate a strong random secret for local JWT signing.
  $bytes = New-Object byte[] 32
  [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
  $jwt = [Convert]::ToBase64String($bytes)
  Set-EnvValue -Key "JWT_SECRET" -Value $jwt
  Write-Host "Generated JWT_SECRET for local dev (.env)." -ForegroundColor Green
}

$bootEmail = Get-EnvValue "BOOTSTRAP_ADMIN_EMAIL"
if (-not $bootEmail) {
  Set-EnvValue -Key "BOOTSTRAP_ADMIN_EMAIL" -Value "admin@coffeestudio.com"
}

$bootPw = Get-EnvValue "BOOTSTRAP_ADMIN_PASSWORD"
if (-not $bootPw -or $bootPw -eq "adminadmin") {
  $bootPw = New-RandomSecret
  Set-EnvValue -Key "BOOTSTRAP_ADMIN_PASSWORD" -Value $bootPw
  Write-Host "Generated BOOTSTRAP_ADMIN_PASSWORD for local dev (.env)." -ForegroundColor Green
}

$grafanaPw = Get-EnvValue "GRAFANA_ADMIN_PASSWORD"
if (-not $grafanaPw -or $grafanaPw -eq "adminadmin") {
  Set-EnvValue -Key "GRAFANA_ADMIN_PASSWORD" -Value (New-RandomSecret)
}

$keycloakPw = Get-EnvValue "KEYCLOAK_ADMIN_PASSWORD"
if (-not $keycloakPw -or $keycloakPw -eq "adminadmin") {
  Set-EnvValue -Key "KEYCLOAK_ADMIN_PASSWORD" -Value (New-RandomSecret)
}

$grafanaAnon = Get-EnvValue "GRAFANA_ANON_ENABLED"
if (-not $grafanaAnon -or $grafanaAnon -eq "true") {
  Set-EnvValue -Key "GRAFANA_ANON_ENABLED" -Value "false"
}

Write-Host "Stopping old containers (if any) ..." -ForegroundColor Cyan
& docker compose down | Out-Host

Write-Host "Building images (no-cache for apps/api/worker/beat to ensure deps like email-validator are installed) ..." -ForegroundColor Cyan
& docker compose build --no-cache backend worker beat | Out-Host

Write-Host "Starting stack ..." -ForegroundColor Cyan
& docker compose up -d --build | Out-Host

Write-Host "Waiting 3 seconds for backend to come up ..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

Write-Host "Running DB migrations ..." -ForegroundColor Cyan
& docker compose exec backend alembic upgrade head | Out-Host

Write-Host "Bootstrapping dev admin (safe to run multiple times) ..." -ForegroundColor Cyan
try {
  Invoke-RestMethod -Method Post -Uri "http://localhost:8000/auth/dev/bootstrap" | Out-Host
} catch {
  Write-Host "Bootstrap call failed (maybe already bootstrapped). Continuing..." -ForegroundColor Yellow
}

Write-Host "Health check ..." -ForegroundColor Cyan
try {
  $h = Invoke-RestMethod -Uri "http://localhost:8000/health"
  Write-Host ("Backend health: " + ($h | ConvertTo-Json -Compress)) -ForegroundColor Green
} catch {
  Write-Host "Health check failed. Showing last backend logs:" -ForegroundColor Red
  & docker compose logs --tail 120 backend | Out-Host
  exit 1
}

Write-Host "Open UI: http://localhost:3000" -ForegroundColor Green
Write-Host "Open API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ("Login (dev): admin@coffeestudio.com / {0}" -f $bootPw) -ForegroundColor Green


Write-Host "MAX stack: run .\scripts\win\03_max_stack_up.ps1" -ForegroundColor Yellow
