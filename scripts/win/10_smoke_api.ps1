param(
  [string]$Base = "http://api.localhost"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Credentials aus Umgebungsvariablen lesen
$Email = $env:SMOKE_TEST_EMAIL
$Password = $env:SMOKE_TEST_PASSWORD

if (-not $Email -or -not $Password) {
  # Fallback auf Standardwerte für lokale Entwicklung
  Write-Warning "SMOKE_TEST_EMAIL und SMOKE_TEST_PASSWORD nicht gesetzt. Verwende Standard-Credentials für lokale Entwicklung."
  $Email = "admin@coffeestudio.com"
  $Password = "adminadmin"
}

# Avoid proxy surprises for localhost domains
$env:NO_PROXY="localhost,127.0.0.1,::1,.localhost,api.localhost,ui.localhost"
$env:HTTP_PROXY=""
$env:HTTPS_PROXY=""

function CurlRaw {
  param(
    [Parameter(Mandatory=$true)][ValidateSet("GET","POST","PUT","PATCH","DELETE")] [string]$Method,
    [Parameter(Mandatory=$true)][string]$Url,
    [Parameter(Mandatory=$false)][string]$JsonBody = $null,
    [Parameter(Mandatory=$false)][hashtable]$Headers = @{}
  )

  $args = @("-sS", "-4", "--noproxy", "*", "-X", $Method, $Url, "-H", "Accept: application/json")

  foreach ($k in $Headers.Keys) {
    $args += @("-H", ("{0}: {1}" -f $k, $Headers[$k]))
  }

  if ($null -ne $JsonBody -and $Method -ne "GET") {
    $args += @("-H", "Content-Type: application/json", "--data-binary", "@-")
    return ($JsonBody | & curl.exe @args)
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
    $h = JsonGet ("{0}/health" -f $B)
    return ($h -and $h.status -eq "ok")
  } catch { return $false }
}

# Base fallback
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