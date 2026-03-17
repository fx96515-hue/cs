param(
    [switch]$Apply,
    [switch]$DockerPrune
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot

$pathsToClean = @(
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "apps/api/.mypy_cache",
    "apps/api/.ruff_cache",
    "apps/web/logs",
    "apps/api/.qa_reports"
)

$filePatterns = @(
    "*.log",
    "*.sarif",
    "bandit-report.json",
    "trivy-*-results.sarif"
)

Write-Host "== CoffeeStudio Local Cleanup =="
Write-Host "Repo: $repoRoot"
Write-Host "Mode: $([string]::Join('', @($(if ($Apply) {'APPLY'} else {'DRY-RUN'}), $(if ($DockerPrune) {' + DOCKER-PRUNE'} else {''}))))"

foreach ($target in $pathsToClean) {
    if (Test-Path $target) {
        if ($Apply) {
            Remove-Item -Recurse -Force $target
            Write-Host "[deleted dir] $target"
        } else {
            Write-Host "[would delete dir] $target"
        }
    }
}

foreach ($pattern in $filePatterns) {
    $hits = Get-ChildItem -Path . -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue
    foreach ($hit in $hits) {
        $rel = Resolve-Path -Relative $hit.FullName
        if ($Apply) {
            Remove-Item -Force $hit.FullName
            Write-Host "[deleted file] $rel"
        } else {
            Write-Host "[would delete file] $rel"
        }
    }
}

if ($DockerPrune) {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Warning "Docker CLI not found. Skipping docker prune."
        exit 0
    }

    Write-Host "`n== Docker Usage (before) =="
    docker system df

    if ($Apply) {
        Write-Host "`nRunning docker image prune -af ..."
        docker image prune -af
        Write-Host "`nRunning docker system prune -af ..."
        docker system prune -af
    } else {
        Write-Host "`n[dry-run] Docker prune would run:"
        Write-Host "  docker image prune -af"
        Write-Host "  docker system prune -af"
    }

    Write-Host "`n== Docker Usage (after) =="
    docker system df
}

Write-Host "`nCleanup finished."
