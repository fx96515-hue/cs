param(
  [string]$Repo = ""
)

$ErrorActionPreference = "Stop"

if (-not $Repo) {
  $Repo = gh repo view --json nameWithOwner -q .nameWithOwner
}

$labels = @(
  @{ name = "p0-critical"; color = "b60205"; desc = "Kritischer Incident / Produktionsproblem" },
  @{ name = "p1-high"; color = "d93f0b"; desc = "Hohe Priorität" },
  @{ name = "p2-medium"; color = "fbca04"; desc = "Mittlere Priorität" },
  @{ name = "p3-low"; color = "0e8a16"; desc = "Nice-to-have" },
  @{ name = "apps/api"; color = "1d76db"; desc = "Backend / API" },
  @{ name = "frontend"; color = "5319e7"; desc = "Frontend / UI" },
  @{ name = "infra"; color = "0052cc"; desc = "Docker / Infra / Runtime" },
  @{ name = "ci-cd"; color = "c5def5"; desc = "CI/CD und Workflows" },
  @{ name = "security"; color = "b60205"; desc = "Security / Hardening" },
  @{ name = "docs"; color = "0e8a16"; desc = "Dokumentation" },
  @{ name = "production-alert"; color = "e11d21"; desc = "Produktion / Health Alarm" },
  @{ name = "hardening"; color = "f9d0c4"; desc = "Qualität / Stabilisierung" }
)

foreach ($l in $labels) {
  $exists = gh label list --repo $Repo --search $l.name --json name -q ".[].name"
  if ($exists -match "^$([regex]::Escape($l.name))$") {
    gh label edit $l.name --repo $Repo --color $l.color --description $l.desc | Out-Null
    Write-Host "Updated label: $($l.name)"
  } else {
    gh label create $l.name --repo $Repo --color $l.color --description $l.desc | Out-Null
    Write-Host "Created label: $($l.name)"
  }
}
Write-Host "Done."
