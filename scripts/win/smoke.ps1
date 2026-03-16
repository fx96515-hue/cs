# CoffeeStudio Windows Smoke Test (PowerShell)
# Usage: .\scripts\win\smoke.ps1
# Requires: Docker Desktop running, stack already started

$ErrorActionPreference = "Stop"
$BaseUrl = if ($env:BASE_URL) { $env:BASE_URL } else { "http://localhost:8000" }

function Get-DotEnvValue {
  param([Parameter(Mandatory=$true)][string]$Key)
  $repoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
  $envPath = Join-Path $repoRoot ".env"
  if (-not (Test-Path $envPath)) { return $null }
  $line = Get-Content $envPath | Where-Object { $_ -match "^$([regex]::Escape($Key))=" } | Select-Object -First 1
  if (-not $line) { return $null }
  return ($line -split "=", 2)[1]
}

$bootEmail = if ($env:BOOTSTRAP_ADMIN_EMAIL) { $env:BOOTSTRAP_ADMIN_EMAIL } else { Get-DotEnvValue "BOOTSTRAP_ADMIN_EMAIL" }
$bootPassword = if ($env:BOOTSTRAP_ADMIN_PASSWORD) { $env:BOOTSTRAP_ADMIN_PASSWORD } else { Get-DotEnvValue "BOOTSTRAP_ADMIN_PASSWORD" }

if (-not $bootEmail -or -not $bootPassword) {
  throw "BOOTSTRAP_ADMIN_EMAIL/BOOTSTRAP_ADMIN_PASSWORD fehlen. Fuehre zuerst run_windows.ps1 aus oder setze die Werte in .env."
}

Write-Host "`n===== CoffeeStudio Smoke Test (Windows) =====" -ForegroundColor Cyan

Write-Host "`n[1/5] Backend health check..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -TimeoutSec 10
    if ($health.status -eq "ok") {
        Write-Host "  Backend healthy: $($health | ConvertTo-Json -Compress)" -ForegroundColor Green
    } else {
        Write-Host "  Unexpected health response" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  Backend not reachable: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n[2/5] DB migrations..." -ForegroundColor Yellow
& docker compose exec -T backend alembic upgrade head 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Migration fehlgeschlagen" -ForegroundColor Red
    exit 1
}
Write-Host "  Migrations OK" -ForegroundColor Green

Write-Host "`n[3/5] Dev bootstrap admin..." -ForegroundColor Yellow
try {
    $bootstrap = Invoke-RestMethod -Method Post -Uri "$BaseUrl/auth/dev/bootstrap" -TimeoutSec 15
    Write-Host "  Bootstrap: $($bootstrap | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
    Write-Host "  Bootstrap-Fehler (evtl. deaktiviert oder bereits vorhanden): $_" -ForegroundColor Yellow
}

Write-Host "`n[4/5] Admin login..." -ForegroundColor Yellow
try {
    $loginBody = @{ email = $bootEmail; password = $bootPassword } | ConvertTo-Json
    $loginResult = Invoke-RestMethod -Method Post -Uri "$BaseUrl/auth/login" -ContentType "application/json" -Body $loginBody -TimeoutSec 10
    $token = $loginResult.access_token
    if ($token) {
        Write-Host "  Login OK, Token erhalten ($($token.Length) Zeichen)" -ForegroundColor Green
    } else {
        Write-Host "  Kein Token erhalten" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  Login fehlgeschlagen: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n[5/5] Authenticated API calls..." -ForegroundColor Yellow
$headers = @{ Authorization = "Bearer $token" }
try {
    $null = Invoke-RestMethod -Uri "$BaseUrl/cooperatives/" -Headers $headers -TimeoutSec 10
    Write-Host "  GET /cooperatives/ OK" -ForegroundColor Green
    $null = Invoke-RestMethod -Uri "$BaseUrl/roasters/" -Headers $headers -TimeoutSec 10
    Write-Host "  GET /roasters/ OK" -ForegroundColor Green
} catch {
    Write-Host "  API-Aufruf fehlgeschlagen: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n[Bonus] Frontend erreichbar..." -ForegroundColor Yellow
try {
    $fe = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 10 -UseBasicParsing
    Write-Host "  Frontend OK (Status: $($fe.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  Frontend nicht erreichbar (evtl. noch am Starten): $_" -ForegroundColor Yellow
}

Write-Host "`n===== Smoke Test abgeschlossen =====" -ForegroundColor Cyan
Write-Host "Alle Gates bestanden." -ForegroundColor Green
