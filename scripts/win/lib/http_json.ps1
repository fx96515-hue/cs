Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function JsonInvoke {
  param(
    [Parameter(Mandatory=$true)][ValidateSet("GET","POST","PUT","PATCH","DELETE")] [string]$Method,
    [Parameter(Mandatory=$true)][string]$Url,
    [Parameter(Mandatory=$false)]$Body = $null,
    [Parameter(Mandatory=$false)][hashtable]$Headers = @{}
  )

  $args = @("-sS", "-X", $Method, $Url, "-H", "Accept: application/json")

  foreach ($k in $Headers.Keys) {
    $args += @("-H", ("${k}: " + $Headers[$k]))
  }

  if ($null -ne $Body -and $Method -ne "GET") {
    $json = ($Body | ConvertTo-Json -Depth 50 -Compress)
    $args += @("-H", "Content-Type: application/json", "--data-binary", "@-")
    $out = $json | & curl.exe @args
  } else {
    $out = & curl.exe @args
  }

  if ([string]::IsNullOrWhiteSpace($out)) { return $null }
  try { return $out | ConvertFrom-Json } catch { return $out }
}

function JsonGet   { param([string]$Url,[hashtable]$Headers=@{}) JsonInvoke -Method "GET"   -Url $Url -Headers $Headers }
function JsonPost  { param([string]$Url,$Body,[hashtable]$Headers=@{}) JsonInvoke -Method "POST"  -Url $Url -Body $Body -Headers $Headers }
function JsonPut   { param([string]$Url,$Body,[hashtable]$Headers=@{}) JsonInvoke -Method "PUT"   -Url $Url -Body $Body -Headers $Headers }
function JsonPatch { param([string]$Url,$Body,[hashtable]$Headers=@{}) JsonInvoke -Method "PATCH" -Url $Url -Body $Body -Headers $Headers }
