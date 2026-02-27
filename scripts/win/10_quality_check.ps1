Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Get-Location).Path

Write-Host "== CoffeeStudio Quality Check ==" -ForegroundColor Cyan

# --- Python venv ---
$VenvPath = Join-Path $RepoRoot ".venv"
$Py = Join-Path $VenvPath "Scripts\python.exe"

if (-not (Test-Path $Py)) {
  Write-Host "Creating venv at $VenvPath" -ForegroundColor Yellow
  python -m venv $VenvPath
}

Write-Host "Updating pip" -ForegroundColor Yellow
& $Py -m pip install --upgrade pip

Write-Host "Installing backend dependencies" -ForegroundColor Yellow
& $Py -m pip install -r (Join-Path $RepoRoot "apps\api\requirements.txt")
if (Test-Path (Join-Path $RepoRoot "apps\api\requirements-dev.txt")) {
  & $Py -m pip install -r (Join-Path $RepoRoot "apps\api\requirements-dev.txt")
} else {
  & $Py -m pip install ruff mypy pytest pytest-asyncio
}

Write-Host "Ruff (lint)" -ForegroundColor Yellow
& $Py -m ruff check (Join-Path $RepoRoot "apps\api")

Write-Host "Ruff (format check)" -ForegroundColor Yellow
& $Py -m ruff format --check (Join-Path $RepoRoot "apps\api\app") (Join-Path $RepoRoot "apps\api\tests")

Write-Host "Mypy (typecheck)" -ForegroundColor Yellow
& $Py -m mypy --config-file (Join-Path $RepoRoot "mypy.ini") (Join-Path $RepoRoot "apps\api\app")

Write-Host "Pytest" -ForegroundColor Yellow
$proc = Start-Process -FilePath $Py -ArgumentList @("-m","pytest","-q") -NoNewWindow -PassThru -Wait
if ($proc.ExitCode -ne 0 -and $proc.ExitCode -ne 5) {
  throw "pytest failed with exit code $($proc.ExitCode)"
}

# --- Frontend ---
if (Test-Path (Join-Path $RepoRoot "apps\web\package.json")) {
  Push-Location (Join-Path $RepoRoot "apps\web")
  try {
    Write-Host "Installing frontend dependencies" -ForegroundColor Yellow
    npm ci --no-fund --no-audit

    Write-Host "Frontend lint" -ForegroundColor Yellow
    npm run lint

    Write-Host "Frontend build" -ForegroundColor Yellow
    npm run build
  } finally {
    Pop-Location
  }
} else {
  Write-Host "Frontend not found - skipping" -ForegroundColor DarkYellow
}

Write-Host "\nAll checks done ✅" -ForegroundColor Green
