param(
  [Parameter(Mandatory = $true)][string]$Branch,
  [Parameter(Mandatory = $true)][string]$CommitMessage,
  [Parameter(Mandatory = $true)][string]$PrTitle,
  [int]$IssueNumber = 0,
  [string]$Labels = "",
  [switch]$Draft,
  [switch]$SkipChecks,
  [string]$PrBodyFile = ""
)

$ErrorActionPreference = "Stop"

function Assert-CleanGitState {
  $status = git status --porcelain
  if ($LASTEXITCODE -ne 0) { throw "git status fehlgeschlagen." }
  if ($status) {
    throw "Arbeitsverzeichnis ist nicht sauber. Bitte zuerst committen/stashen."
  }
}

function Run-Cmd {
  param([string]$Name, [scriptblock]$Block, [switch]$AllowFail)
  Write-Host "==> $Name"
  & $Block
  if (($LASTEXITCODE -ne 0) -and (-not $AllowFail)) {
    throw "$Name fehlgeschlagen."
  }
}

function Try-Run {
  param([string]$Name, [scriptblock]$Block)
  try {
    Run-Cmd -Name $Name -Block $Block -AllowFail:$false
  } catch {
    Write-Warning "$Name fehlgeschlagen: $($_.Exception.Message)"
    throw
  }
}

function Run-HeuristicChecks {
  if ($SkipChecks) {
    Write-Host "Checks übersprungen (-SkipChecks)."
    return
  }

  if (Test-Path "apps/web/package.json") {
    Push-Location "frontend"
    if (Test-Path "package-lock.json" -or Test-Path "npm-shrinkwrap.json") {
      Run-Cmd "Frontend install (npm ci)" { npm ci } -AllowFail
    }
    Run-Cmd "Frontend lint (npm run lint)" { npm run lint } -AllowFail
    Run-Cmd "Frontend typecheck (npm run typecheck)" { npm run typecheck } -AllowFail
    Run-Cmd "Frontend build (npm run build)" { npm run build } -AllowFail
    Pop-Location
  }

  if (Test-Path "apps/api/pyproject.toml" -or Test-Path "apps/api/requirements.txt") {
    Push-Location "apps/api"
    if (Test-Path "requirements.txt") {
      Run-Cmd "Backend install (pip install -r requirements.txt)" { python -m pip install -r requirements.txt } -AllowFail
    }
    Run-Cmd "Backend tests (pytest)" { python -m pytest } -AllowFail
    Pop-Location
  }

  if (Test-Path "docker-compose.yml" -or Test-Path "compose.yml") {
    $composeFile = (Test-Path "docker-compose.yml") ? "docker-compose.yml" : "compose.yml"
    Run-Cmd "Docker compose config" { docker compose -f $composeFile config } -AllowFail
  }
}

function Build-PrBody {
  param([string]$FilePath)

  if ($FilePath -and (Test-Path $FilePath)) {
    return (Get-Content $FilePath -Raw)
  }

  $issueLine = if ($IssueNumber -gt 0) { "Bezug: #$IssueNumber" } else { "-" }
  return @"
## Problem
- <kurz beschreiben>
- $issueLine

## Ursache
- <Root Cause>

## Lösung
- <Umsetzung>

## Betroffene Bereiche
- [ ] Backend
- [ ] Frontend
- [ ] Infra/CI
- [ ] Doku
- [ ] Security

## Testnachweis
- [ ] Lint
- [ ] Typecheck
- [ ] Tests
- [ ] Build
- [ ] Smoke/Health lokal
- [ ] Docker Compose Start (falls relevant)

## Risiken
- <Risiko>

## Rollback
- Revert PR / Branch

## Doku-Updates
- [ ] CHANGELOG
- [ ] STATUS / Operations Doku
- [ ] README
- [ ] Keine Doku-Änderung nötig

## Follow-ups
- <optional>
"@
}

# Preconditions
Run-Cmd "GitHub CLI Auth Check" { gh auth status } 
Assert-CleanGitState

# Branch
Run-Cmd "Branch erstellen" { git checkout -b $Branch }

# Checks
Run-HeuristicChecks

# Stage + Commit
Run-Cmd "git add" { git add -A }
Run-Cmd "git commit" { git commit -m $CommitMessage }

# Push
Run-Cmd "git push" { git push -u origin $Branch }

# PR Body
$body = Build-PrBody -FilePath $PrBodyFile
$tmp = New-TemporaryFile
Set-Content -Path $tmp -Value $body -Encoding UTF8

# PR Create
$prArgs = @("pr", "create", "--title", $PrTitle, "--body-file", $tmp.FullName)
if ($Draft) { $prArgs += "--draft" }
if ($IssueNumber -gt 0) { $prArgs += @("--head", $Branch) }

Run-Cmd "PR erstellen" { gh @prArgs }

# Labels (optional)
if ($Labels) {
  $labelList = $Labels.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
  if ($labelList.Count -gt 0) {
    $prNumber = gh pr view --json number -q .number
    foreach ($label in $labelList) {
      Run-Cmd "PR Label $label" { gh pr edit $prNumber --add-label $label } -AllowFail
    }
  }
}

Write-Host ""
Write-Host "✅ Autopilot PR Flow abgeschlossen."
Write-Host "Prüfe jetzt auf GitHub: Files changed, CI-Status, PR-Text, Merge-Readiness."
