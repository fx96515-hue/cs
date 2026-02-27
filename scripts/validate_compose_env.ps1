<#
Validates presence of the compose env file expected by the enterprise compose.
Exits with code 0 if found or created by fallback; 1 otherwise.

Usage:
  .\scripts\validate_compose_env.ps1
#>

$ErrorActionPreference = 'Stop'

$repoRoot = (Get-Location).Path
$expected1 = Join-Path $repoRoot 'ops\.env.enterprise.example'
$expected2 = Join-Path $repoRoot '.env.enterprise.example'

if (Test-Path $expected1) {
    Write-Host "Found expected env file: $expected1"
    exit 0
}

if (Test-Path $expected2) {
    Write-Host "Found root example env file: $expected2; copying to $expected1"
    New-Item -ItemType Directory -Path (Split-Path $expected1) -Force | Out-Null
    Copy-Item $expected2 $expected1 -Force
    exit 0
}

Write-Error "Compose env example not found in ops or repo root. Please add .env.enterprise.example."
exit 1
