Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Get-Location).Path
$Ts = Get-Date -Format "yyyyMMdd_HHmmss"
$OutDir = Join-Path $RepoRoot "backups\bundle_$Ts"
$ZipPath = Join-Path $RepoRoot "backups\coffeestudio_backup_$Ts.zip"

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function SafeRun {
  param(
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][scriptblock]$Block
  )
  try {
    $out = & $Block 2>&1 | Out-String
    $out | Set-Content -Encoding UTF8 (Join-Path $OutDir $Name)
  } catch {
    ("ERROR: " + $_.Exception.Message + "`n" + ($_.ScriptStackTrace | Out-String)) |
      Set-Content -Encoding UTF8 (Join-Path $OutDir $Name)
  }
}

function CopyIfExists {
  param([Parameter(Mandatory=$true)][string]$RelPath)
  $src = Join-Path $RepoRoot $RelPath
  if (Test-Path $src) {
    $dst = Join-Path $OutDir $RelPath
    $dstDir = Split-Path -Parent $dst
    New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
    Copy-Item -Force -Recurse -Path $src -Destination $dst
  }
}

# --- Copy key project artifacts (NO SECRETS) ---
CopyIfExists "docker-compose.yml"
CopyIfExists "docker-compose.stack.yml"
CopyIfExists "docker-compose.override.yml"
CopyIfExists "docker-compose.ops.yml"
CopyIfExists "docker-compose.traefik.admin.yml"
CopyIfExists "compose"
CopyIfExists "scripts"
CopyIfExists "README.md"
CopyIfExists "docs"
CopyIfExists ".env.example"

# Repo hygiene / tooling
CopyIfExists ".github"
CopyIfExists ".gitignore"
CopyIfExists ".dockerignore"
CopyIfExists "mypy.ini"

# Infra / stacks (only if present)
CopyIfExists "ops"
CopyIfExists "infra"
CopyIfExists "traefik"
CopyIfExists "prometheus"

# Backend
CopyIfExists "apps\api\Dockerfile"
CopyIfExists "apps\api\app"
CopyIfExists "apps\api\alembic"
CopyIfExists "apps\api\migrations"
CopyIfExists "apps\api\requirements.txt"
CopyIfExists "apps\api\requirements-dev.txt"
CopyIfExists "apps\api\pyproject.toml"
CopyIfExists "apps\api\alembic.ini"

# Frontend (optional)
CopyIfExists "apps\web\Dockerfile"
CopyIfExists "frontend"
CopyIfExists "ui"
CopyIfExists "ui\.env.example"
CopyIfExists "apps\web\.env.example"

# --- Clean junk / caches / secrets from bundle ---
$JunkDirs = @(
  "__pycache__",
  ".pytest_cache",
  ".mypy_cache",
  ".ruff_cache",
  "node_modules",
  ".next",
  "dist",
  "out",
  ".venv",
  "venv"
)
foreach ($d in $JunkDirs) {
  Get-ChildItem -Path $OutDir -Recurse -Force -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq $d } |
    ForEach-Object { Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $_.FullName }
}

# Remove compiled Python artifacts
Get-ChildItem -Path $OutDir -Recurse -Force -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Extension -in @(".pyc", ".pyo") } |
  ForEach-Object { Remove-Item -Force -ErrorAction SilentlyContinue $_.FullName }

# Remove env files (keep *.example)
Get-ChildItem -Path $OutDir -Recurse -Force -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -like ".env*" -and $_.Name -notlike "*.example" } |
  ForEach-Object { Remove-Item -Force -ErrorAction SilentlyContinue $_.FullName }

# --- Runtime / diagnostics ---
SafeRun "00_pwd.txt" { $RepoRoot }
SafeRun "01_powershell_version.txt" { $PSVersionTable | Format-List | Out-String }
SafeRun "02_docker_version.txt" { docker version }
SafeRun "03_docker_info.txt" { docker info }
SafeRun "04_compose_version.txt" { docker compose version }
SafeRun "05_compose_config.txt" { docker compose config }
SafeRun "06_compose_ps.txt" { docker compose ps }

SafeRun "10_logs_backend.txt" { docker compose logs --no-color --tail 1200 backend }
SafeRun "11_logs_worker.txt"  { docker compose logs --no-color --tail 1200 worker }
SafeRun "12_logs_beat.txt"    { docker compose logs --no-color --tail 1200 beat }
SafeRun "13_logs_frontend.txt"{ docker compose logs --no-color --tail 1200 frontend }
SafeRun "14_logs_traefik.txt" { docker compose logs --no-color --tail 1200 traefik }
SafeRun "15_logs_postgres.txt"{ docker compose logs --no-color --tail 1200 postgres }
SafeRun "16_logs_redis.txt"   { docker compose logs --no-color --tail 1200 redis }

# --- DB schema dump (best effort) ---
SafeRun "20_db_schema_pg_dump.txt" {
  docker compose exec -T postgres sh -lc 'pg_dump --schema-only -U "${POSTGRES_USER:-coffeestudio}" "${POSTGRES_DB:-coffeestudio}"'
}

# --- API quick checks ---
SafeRun "30_api_health.txt" { curl.exe -sS http://api.localhost/health }
SafeRun "31_ui_login_httpcode.txt" { curl.exe -sS -o NUL -w "HTTP %{http_code}`n" http://ui.localhost/login }

# --- Zip ---
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ZipPath) | Out-Null
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
Compress-Archive -Path (Join-Path $OutDir "*") -DestinationPath $ZipPath -Force

Write-Host "BACKUP DONE ✅"
Write-Host ("ZIP: " + $ZipPath)
Write-Host ("DIR: " + $OutDir)
