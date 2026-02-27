<#
CoffeeStudio "maximum" stack bootstrap (Windows).

This starts:
  - API (FastAPI)
  - UI (Next.js)
  - Postgres + Redis
  - Traefik reverse proxy + optional ops tools (Grafana/Metabase/Portainer/Keycloak/Appsmith)

Run in PowerShell.

Usage:
  .\scripts\win\02_stack_up.ps1

After it finishes, open:
  http://ui.localhost
  http://api.localhost/health
  http://traefik.localhost/dashboard/
#>

$ErrorActionPreference = "Stop"

function Assert-Command($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "Missing command: $name"
  }
}

Assert-Command docker

Write-Host "== Docker check ==" -ForegroundColor Cyan
docker version | Out-Null

Write-Host "== Build + Up (stack profile) ==" -ForegroundColor Cyan
docker compose -f docker-compose.yml -f docker-compose.stack.yml --profile stack up -d --build

Write-Host "== Health checks ==" -ForegroundColor Cyan

function Curl-Code($url, $hostHeader=$null) {
  $args = @("-sS", "-o", "NUL", "-w", "%{http_code}", $url)
  if ($hostHeader) { $args = @("-sS", "-o", "NUL", "-w", "%{http_code}", "-H", "Host: $hostHeader", $url) }
  $code = & curl.exe @args
  return $code
}

$apiCode = Curl-Code "http://127.0.0.1/health" "api.localhost"
$uiCode  = Curl-Code "http://127.0.0.1/" "ui.localhost"

Write-Host "api.localhost/health => $apiCode" -ForegroundColor Yellow
Write-Host "ui.localhost/ => $uiCode" -ForegroundColor Yellow

Write-Host "OK. Open http://ui.localhost" -ForegroundColor Green
