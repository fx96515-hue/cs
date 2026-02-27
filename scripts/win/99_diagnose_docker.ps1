<#
Quick Docker diagnostics helper (Windows).

Usage:
  .\scripts\win\99_diagnose_docker.ps1
#>

$ErrorActionPreference = "Continue"
Set-Location -Path $PSScriptRoot
Set-Location -Path "..\.."

function New-Timestamp() { (Get-Date).ToString("yyyyMMdd_HHmmss") }
function Ensure-Dir($path) { if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path | Out-Null } }

Ensure-Dir ".\diagnostics"
$ts = New-Timestamp
$outDir = ".\diagnostics\docker_${ts}"
Ensure-Dir $outDir

docker version | Out-File (Join-Path $outDir "docker_version.txt")
docker info 2>&1 | Out-File (Join-Path $outDir "docker_info.txt")
docker context ls 2>&1 | Out-File (Join-Path $outDir "docker_context_ls.txt")
docker compose version 2>&1 | Out-File (Join-Path $outDir "compose_version.txt")

Write-Host "Diagnostics written: $outDir" -ForegroundColor Yellow
