param(
    [string]$RepoRoot = "."
)

$ErrorActionPreference = "Stop"

Push-Location $RepoRoot
try {
    Write-Host "== Wrapper Usage Audit ==" -ForegroundColor Cyan

    Write-Host "`n[1] app.api.routes references" -ForegroundColor Yellow
    rg "from app\.api\.routes|app\.api\.routes\." apps tests -n
    if ($LASTEXITCODE -eq 1) {
        Write-Host "No wrapper references found." -ForegroundColor Green
    }

    Write-Host "`n[2] app.schemas references" -ForegroundColor Yellow
    rg "from app\.schemas\.|app\.schemas\." apps tests -n
    if ($LASTEXITCODE -eq 1) {
        Write-Host "No schema-wrapper references found." -ForegroundColor Green
    }
}
finally {
    Pop-Location
}

