# CoffeeStudio Windows Smoke Test (PowerShell)
# Usage: .\scripts\win\smoke.ps1
# Requires: Docker Desktop running, stack already started

$ErrorActionPreference = "Stop"
$BaseUrl = if ($env:BASE_URL) { $env:BASE_URL } else { "http://localhost:8000" }

Write-Host "`n===== CoffeeStudio Smoke Test (Windows) =====" -ForegroundColor Cyan

# Gate 1: Backend Health
Write-Host "`n[1/5] Backend health check..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -TimeoutSec 10
    if ($health.status -eq "ok") {
        Write-Host "  ✅ Backend healthy: $($health | ConvertTo-Json -Compress)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Unexpected health response" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ❌ Backend not reachable: $_" -ForegroundColor Red
    Write-Host "  💡 Tipp: Ist 'docker compose up -d' gelaufen?" -ForegroundColor Yellow
    exit 1
}

# Gate 2: DB Migrations
Write-Host "`n[2/5] DB migrations..." -ForegroundColor Yellow
& docker compose exec -T backend alembic upgrade head 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Migration fehlgeschlagen" -ForegroundColor Red
    exit 1
}
Write-Host "  ✅ Migrations OK" -ForegroundColor Green

# Gate 3: Bootstrap Admin
Write-Host "`n[3/5] Dev bootstrap admin..." -ForegroundColor Yellow
try {
    $bootstrap = Invoke-RestMethod -Method Post -Uri "$BaseUrl/auth/dev/bootstrap" -TimeoutSec 15
    Write-Host "  ✅ Bootstrap: $($bootstrap | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ Bootstrap-Fehler (evtl. bereits vorhanden): $_" -ForegroundColor Yellow
}

# Gate 4: Login
Write-Host "`n[4/5] Admin login..." -ForegroundColor Yellow
$bootEmail = "admin@coffeestudio.com"
$bootPassword = if ($env:BOOTSTRAP_ADMIN_PASSWORD) { $env:BOOTSTRAP_ADMIN_PASSWORD } else { "adminadmin" }
try {
    $loginBody = @{ email = $bootEmail; password = $bootPassword } | ConvertTo-Json
    $loginResult = Invoke-RestMethod -Method Post -Uri "$BaseUrl/auth/login" -ContentType "application/json" -Body $loginBody -TimeoutSec 10
    $token = $loginResult.access_token
    if ($token) {
        Write-Host "  ✅ Login OK, Token erhalten (${($token.Length)} Zeichen)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Kein Token erhalten" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ❌ Login fehlgeschlagen: $_" -ForegroundColor Red
    exit 1
}

# Gate 5: Authenticated API
Write-Host "`n[5/5] Authenticated API calls..." -ForegroundColor Yellow
$headers = @{ Authorization = "Bearer $token" }
try {
    $coops = Invoke-RestMethod -Uri "$BaseUrl/cooperatives" -Headers $headers -TimeoutSec 10
    Write-Host "  ✅ GET /cooperatives OK" -ForegroundColor Green
    $roasters = Invoke-RestMethod -Uri "$BaseUrl/roasters" -Headers $headers -TimeoutSec 10
    Write-Host "  ✅ GET /roasters OK" -ForegroundColor Green
} catch {
    Write-Host "  ❌ API-Aufruf fehlgeschlagen: $_" -ForegroundColor Red
    exit 1
}

# Frontend check
Write-Host "`n[Bonus] Frontend erreichbar..." -ForegroundColor Yellow
try {
    $fe = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 10 -UseBasicParsing
    Write-Host "  ✅ Frontend OK (Status: $($fe.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ Frontend nicht erreichbar (evtl. noch am Starten): $_" -ForegroundColor Yellow
}

Write-Host "`n===== Smoke Test abgeschlossen =====" -ForegroundColor Cyan
Write-Host "🎉 Alle Gates bestanden!" -ForegroundColor Green
Write-Host ""
Write-Host "Nächste Schritte:" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  Logs:      docker compose logs -f --tail=200" -ForegroundColor White
