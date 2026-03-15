param(
  [string]$Base = "http://api.localhost"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-DotEnvValue {
  param([Parameter(Mandatory=$true)][string]$Key)
  $repoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
  $envPath = Join-Path $repoRoot ".env"
  if (-not (Test-Path $envPath)) { return $null }
  $line = Get-Content $envPath | Where-Object { $_ -match "^$([regex]::Escape($Key))=" } | Select-Object -First 1
  if (-not $line) { return $null }
  return ($line -split "=", 2)[1]
}

$Email = if ($env:SMOKE_TEST_EMAIL) { $env:SMOKE_TEST_EMAIL } else { Get-DotEnvValue "BOOTSTRAP_ADMIN_EMAIL" }
$Password = if ($env:SMOKE_TEST_PASSWORD) { $env:SMOKE_TEST_PASSWORD } else { Get-DotEnvValue "BOOTSTRAP_ADMIN_PASSWORD" }

if (-not $Email -or -not $Password) {
  throw "SMOKE_TEST_EMAIL/SMOKE_TEST_PASSWORD oder BOOTSTRAP_ADMIN_EMAIL/BOOTSTRAP_ADMIN_PASSWORD in .env fehlen."
}

$env:NO_PROXY = "localhost,127.0.0.1,::1,.localhost,api.localhost,ui.localhost"
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""

function CurlRaw {
  param(
    [Parameter(Mandatory=$true)][ValidateSet("GET","POST","PUT","PATCH","DELETE")] [string]$Method,
    [Parameter(Mandatory=$true)][string]$Url,
    [Parameter(Mandatory=$false)][string]$JsonBody = $null,
    [Parameter(Mandatory=$false)][hashtable]$Headers = @{},
    [switch]$QuietErrors
  )

  $args = @("-sS", "-4", "--noproxy", "*", "-X", $Method, $Url, "-H", "Accept: application/json")

  foreach ($k in $Headers.Keys) {
    $args += @("-H", ("{0}: {1}" -f $k, $Headers[$k]))
  }

  if ($null -ne $JsonBody -and $Method -ne "GET") {
    $args += @("-H", "Content-Type: application/json", "--data-binary", "@-")
    if ($QuietErrors) {
      return ($JsonBody | & curl.exe @args 2>$null)
    }
    return ($JsonBody | & curl.exe @args)
  }

  if ($QuietErrors) {
    return (& curl.exe @args 2>$null)
  }
  return (& curl.exe @args)
}

function JsonGet {
  param([string]$Url,[hashtable]$Headers=@{})
  $raw = CurlRaw -Method "GET" -Url $Url -Headers $Headers
  if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
  try { return ($raw | ConvertFrom-Json) } catch { throw ("Non-JSON response from GET {0}`n{1}" -f $Url, $raw) }
}

function JsonPost {
  param([string]$Url,[object]$Body,[hashtable]$Headers=@{})
  $json = ($Body | ConvertTo-Json -Depth 30 -Compress)
  $raw = CurlRaw -Method "POST" -Url $Url -JsonBody $json -Headers $Headers
  if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
  try { return ($raw | ConvertFrom-Json) } catch { throw ("Non-JSON response from POST {0}`n{1}" -f $Url, $raw) }
}

function TryHealth {
  param([string]$B)
  try {
    $raw = CurlRaw -Method "GET" -Url ("{0}/health" -f $B) -QuietErrors
    if ([string]::IsNullOrWhiteSpace($raw)) { return $false }
    $h = $raw | ConvertFrom-Json
    return ($h -and $h.status -eq "ok")
  } catch { return $false }
}

if (-not (TryHealth $Base)) {
  $fallback = "http://127.0.0.1:8000"
  Write-Host ("Base failed, fallback to {0}" -f $fallback)
  $Base = $fallback
}
if (-not (TryHealth $Base)) { throw ("Health failed for Base={0}" -f $Base) }

Write-Host ("== Health ({0})" -f $Base)
(JsonGet ("{0}/health" -f $Base)) | ConvertTo-Json -Depth 10

Write-Host "== Login"
$login = JsonPost ("{0}/auth/login" -f $Base) @{ email=$Email; password=$Password }
if (-not $login) { throw "Login returned empty response" }
if (-not ($login.PSObject.Properties.Name -contains "access_token")) {
  throw ("No access_token in login response:`n{0}" -f ($login | ConvertTo-Json -Depth 10))
}

$AUTH = @{ Authorization = ("Bearer {0}" -f $login.access_token) }

Write-Host "== /auth/me"
(JsonGet ("{0}/auth/me" -f $Base) $AUTH) | ConvertTo-Json -Depth 10

Write-Host "== KB seed"
(JsonPost ("{0}/kb/seed" -f $Base) @{} $AUTH) | ConvertTo-Json -Depth 10

Write-Host "== KB query (logistics/de)"
(JsonGet ("{0}/kb/?category=logistics&language=de" -f $Base) $AUTH) | ConvertTo-Json -Depth 50

Write-Host "SMOKE OK"
