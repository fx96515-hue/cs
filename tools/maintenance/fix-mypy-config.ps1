$ErrorActionPreference = "Stop"

function Backup-File([string]$Path) {
  if (Test-Path $Path) {
    $ts = Get-Date -Format "yyyyMMdd_HHmmss"
    Copy-Item $Path "$Path.bak_$ts" -Force
    Write-Host "Backup: $Path -> $Path.bak_$ts" -ForegroundColor DarkGray
  } else {
    throw "File not found: $Path"
  }
}

function Replace-InFile {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Pattern,
    [Parameter(Mandatory=$true)][AllowEmptyString()][string]$Replacement,
    [Parameter(Mandatory=$true)][string]$Label,
    [int]$Max = 0
  )
  $text = Get-Content $Path -Raw
  $rx = [regex]$Pattern
  $count = $rx.Matches($text).Count

  if ($count -eq 0) {
    Write-Warning "[$Label] Pattern not found in $Path"
    return $false
  }
  if ($Max -gt 0 -and $count -gt $Max) {
    throw "[$Label] Too many matches ($count) in $Path (max $Max)"
  }

  $newText = $rx.Replace($text, $Replacement)
  Set-Content -Path $Path -Value $newText -Encoding UTF8
  Write-Host "[$Label] OK ($count match(es)) -> $Path" -ForegroundColor Green
  return $true
}

# ------------------------------------------------------------
# 1) ecb_fx.py: dt_str can be None -> guard before fromisoformat
# ------------------------------------------------------------
$ecb = "apps\api\app\providers\ecb_fx.py"
Backup-File $ecb

$repEcb = '${indent}if not dt_str:' + "`r`n" +
          '${indent}    continue' + "`r`n" +
          '${indent}observed_at = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)'

$null = Replace-InFile -Path $ecb `
  -Pattern '(?m)^(?<indent>\s*)observed_at\s*=\s*datetime\.fromisoformat\(dt_str\)\.replace\(tzinfo=timezone\.utc\)\s*$' `
  -Replacement $repEcb `
  -Label 'ecb_fx guard dt_str' `
  -Max 10

# ------------------------------------------------------------
# 2) reports.py: latest[k] can be None -> guard access
# ------------------------------------------------------------
$reports = "apps\api\app\services\reports.py"
Backup-File $reports

$null = Replace-InFile -Path $reports `
  -Pattern '(?m)^(?<indent>\s*)"value"\s*:\s*latest\[k\]\.value\s*,\s*$' `
  -Replacement '${indent}"value": (latest[k].value if latest[k] is not None else None),' `
  -Label 'reports guard latest[k].value' `
  -Max 10

$null = Replace-InFile -Path $reports `
  -Pattern '(?m)^(?<indent>\s*)"observed_at"\s*:\s*latest\[k\]\.observed_at\.isoformat\(\)\s*,\s*$' `
  -Replacement '${indent}"observed_at": (latest[k].observed_at.isoformat() if latest[k] is not None else None),' `
  -Label 'reports guard latest[k].observed_at' `
  -Max 10

# ------------------------------------------------------------
# 3) enrichment.py: Union(Cooperative|Roaster) -> avoid attr errors with setattr
# ------------------------------------------------------------
$enrich = "apps\api\app\services\enrichment.py"
Backup-File $enrich

$null = Replace-InFile -Path $enrich `
  -Pattern '(?m)^(?<indent>\s*)entity\.region\s*=\s*(?<rhs>.+?)\s*$' `
  -Replacement '${indent}setattr(entity, "region", ${rhs})' `
  -Label 'enrichment region -> setattr' `
  -Max 20

$null = Replace-InFile -Path $enrich `
  -Pattern '(?m)^(?<indent>\s*)entity\.varieties\s*=\s*(?<rhs>.+?)\s*$' `
  -Replacement '${indent}setattr(entity, "varieties", ${rhs})' `
  -Label 'enrichment varieties -> setattr' `
  -Max 20

$null = Replace-InFile -Path $enrich `
  -Pattern '(?m)^(?<indent>\s*)entity\.certifications\s*=\s*(?<rhs>.+?)\s*$' `
  -Replacement '${indent}setattr(entity, "certifications", ${rhs})' `
  -Label 'enrichment certifications -> setattr' `
  -Max 20

$null = Replace-InFile -Path $enrich `
  -Pattern '(?m)^(?<indent>\s*)entity\.city\s*=\s*(?<rhs>.+?)\s*$' `
  -Replacement '${indent}setattr(entity, "city", ${rhs})' `
  -Label 'enrichment city -> setattr' `
  -Max 20

# ------------------------------------------------------------
# 4) dedup.py: remove unused ignore comment
# ------------------------------------------------------------
$dedup = "apps\api\app\services\dedup.py"
Backup-File $dedup

$null = Replace-InFile -Path $dedup `
  -Pattern '(?m)\s*#\s*type:\s*ignore\[assignment\]\s*$' `
  -Replacement '' `
  -Label 'dedup remove unused ignore' `
  -Max 50

Write-Host "`nOK: patches applied." -ForegroundColor Cyan

