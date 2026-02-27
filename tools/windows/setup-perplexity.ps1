# CoffeeStudio - Perplexity API Setup Script
# Usage: Right-click -> "Run with PowerShell" or execute: .\setup_perplexity.ps1

$ErrorActionPreference = 'Stop'

Write-Host '== CoffeeStudio: Perplexity API Setup ==' -ForegroundColor Cyan

# Determine script directory (fallback to current directory for PowerShell 5 compatibility)
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) {
  $ScriptDir = (Get-Location).Path
}

# Ensure we are in the script directory
Set-Location -Path $ScriptDir

# ====== Step 1: Check that we're in the right directory ======
Write-Host ''
Write-Host '[1/10] Checking directory...' -ForegroundColor Cyan
if (-not (Test-Path 'docker-compose.yml')) {
  Write-Host 'ERROR: docker-compose.yml not found. Please run this script from the project root.' -ForegroundColor Red
  exit 1
}
Write-Host '  [OK] Found docker-compose.yml' -ForegroundColor Green

# ====== Step 2: Check/create .env from .env.example if missing ======
Write-Host ''
Write-Host '[2/10] Checking .env file...' -ForegroundColor Cyan
if (-not (Test-Path '.env')) {
  if (-not (Test-Path '.env.example')) {
    Write-Host 'ERROR: .env.example not found. Cannot create .env.' -ForegroundColor Red
    exit 1
  }
  Write-Host '  No .env found. Creating from .env.example...' -ForegroundColor Yellow
  Copy-Item .env.example .env
  Write-Host '  [OK] Created .env from .env.example' -ForegroundColor Green
} else {
  Write-Host '  [OK] .env already exists' -ForegroundColor Green
}

# ====== Helper Functions (matching run_windows.ps1 pattern) ======
function Set-EnvValue {
  param(
    [Parameter(Mandatory=$true)][string]$Key,
    [Parameter(Mandatory=$true)][string]$Value
  )
  $envPath = Join-Path -Path $ScriptDir -ChildPath '.env'
  $lines = Get-Content -Path $envPath
  $escapedKey = [regex]::Escape($Key)
  $re = "^$escapedKey=.*$"
  $matched = $false
  $newLines = @()
  foreach ($line in $lines) {
    if ($line -match $re) {
      $newLines += "$Key=$Value"
      $matched = $true
    } else {
      $newLines += $line
    }
  }
  if (-not $matched) {
    $newLines += "$Key=$Value"
  }
  Set-Content -Path $envPath -Value $newLines -Encoding UTF8
}

function Get-EnvValue {
  param([Parameter(Mandatory=$true)][string]$Key)
  $envPath = Join-Path -Path $ScriptDir -ChildPath '.env'
  if (-not (Test-Path $envPath)) {
    return $null
  }
  $lines = Get-Content -Path $envPath
  $escapedKey = [regex]::Escape($Key)
  $re = "^$escapedKey="
  foreach ($line in $lines) {
    if ($line -match $re) {
      $parts = $line -split '=', 2
      if ($parts.Length -eq 2) {
        return $parts[1]
      }
      return $null
    }
  }
  return $null
}

# ====== Step 3: Prompt for Perplexity API Key or detect existing ======
Write-Host ''
Write-Host '[3/10] Checking Perplexity API key...' -ForegroundColor Cyan
$existingKey = Get-EnvValue 'PERPLEXITY_API_KEY'

if ($existingKey -and $existingKey.Length -gt 0 -and $existingKey -ne '') {
  $previewLen = [Math]::Min(10, $existingKey.Length)
  $keyPreview = $existingKey.Substring(0, $previewLen)
  Write-Host "  Found existing key: $keyPreview..." -ForegroundColor Yellow
  $response = Read-Host '  Keep this key? (Y/n)'
  if ($response -eq '' -or $response -eq 'Y' -or $response -eq 'y') {
    $apiKey = $existingKey
    Write-Host '  [OK] Using existing key' -ForegroundColor Green
  } else {
    $apiKey = Read-Host '  Enter new Perplexity API Key (starts with pplx-)'
  }
} else {
  Write-Host '  No Perplexity API key found in .env' -ForegroundColor Yellow
  $apiKey = Read-Host '  Enter your Perplexity API Key (starts with pplx-)'
}

# Validate key format
if (-not $apiKey -or $apiKey.Length -eq 0) {
  Write-Host 'ERROR: API key cannot be empty' -ForegroundColor Red
  exit 1
}
if (-not $apiKey.StartsWith('pplx-')) {
  Write-Host 'WARNING: API key should start with pplx-. Continuing anyway...' -ForegroundColor Yellow
}

# ====== Step 4: Write PERPLEXITY_API_KEY into .env ======
Write-Host ''
Write-Host '[4/10] Updating .env with API key...' -ForegroundColor Cyan
Set-EnvValue -Key 'PERPLEXITY_API_KEY' -Value $apiKey
Write-Host '  [OK] Updated PERPLEXITY_API_KEY in .env' -ForegroundColor Green

# ====== Step 5: Ensure PERPLEXITY_MODEL_DISCOVERY is set ======
Write-Host ''
Write-Host '[5/10] Checking PERPLEXITY_MODEL_DISCOVERY...' -ForegroundColor Cyan
$existingModel = Get-EnvValue 'PERPLEXITY_MODEL_DISCOVERY'
if ($existingModel -ne 'sonar-pro') {
  Set-EnvValue -Key 'PERPLEXITY_MODEL_DISCOVERY' -Value 'sonar-pro'
  Write-Host '  [OK] Set PERPLEXITY_MODEL_DISCOVERY=sonar-pro' -ForegroundColor Green
} else {
  Write-Host '  [OK] PERPLEXITY_MODEL_DISCOVERY already set to sonar-pro' -ForegroundColor Green
}

# ====== Step 6: Restart backend, worker, beat containers ======
Write-Host ''
Write-Host '[6/10] Restarting backend, worker, and beat containers...' -ForegroundColor Cyan
try {
  & docker compose restart backend worker beat | Out-Host
  Write-Host '  [OK] Containers restarted' -ForegroundColor Green
} catch {
  $errMsg = $_.Exception.Message
  Write-Host "ERROR: Failed to restart containers: $errMsg" -ForegroundColor Red
  exit 1
}

# ====== Step 7: Wait 5 seconds after restart ======
Write-Host ''
Write-Host '[7/10] Waiting 5 seconds for containers to stabilize...' -ForegroundColor Cyan
Start-Sleep -Seconds 5
Write-Host '  [OK] Wait complete' -ForegroundColor Green

# ====== Step 8: Verify the key is available inside the container ======
Write-Host ''
Write-Host '[8/10] Verifying API key inside backend container...' -ForegroundColor Cyan
try {
  $checkCmd = 'import os; key = os.getenv("PERPLEXITY_API_KEY", ""); print("OK" if key and len(key) > 0 else "MISSING")'
  $result = & docker compose exec -T backend python -c $checkCmd 2>&1
  $result = $result | Out-String
  if ($result -match 'OK') {
    Write-Host '  [OK] API key is available in backend container' -ForegroundColor Green
  } else {
    Write-Host "WARNING: API key verification failed. Result: $result" -ForegroundColor Yellow
    Write-Host '  Continuing anyway...' -ForegroundColor Yellow
  }
} catch {
  $errMsg = $_.Exception.Message
  Write-Host "WARNING: Could not verify API key in container: $errMsg" -ForegroundColor Yellow
  Write-Host '  Continuing anyway...' -ForegroundColor Yellow
}

# ====== Step 9: Get admin JWT token ======
Write-Host ''
Write-Host '[9/10] Getting admin JWT token...' -ForegroundColor Cyan

# First, run bootstrap
Write-Host '  Running bootstrap...' -ForegroundColor Cyan
try {
  $bootstrapResult = Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/auth/dev/bootstrap' -ErrorAction SilentlyContinue
  if ($bootstrapResult.status -eq 'created') {
    Write-Host '  [OK] Admin user created' -ForegroundColor Green
  } else {
    Write-Host '  Admin user already exists (skipped)' -ForegroundColor Yellow
  }
} catch {
  Write-Host '  Admin user already exists or bootstrap failed (continuing)' -ForegroundColor Yellow
}

# Get credentials from .env or use defaults
$adminEmail = Get-EnvValue 'BOOTSTRAP_ADMIN_EMAIL'
if (-not $adminEmail) {
  $adminEmail = 'admin@coffeestudio.com'
}

$adminPassword = Get-EnvValue 'BOOTSTRAP_ADMIN_PASSWORD'
if (-not $adminPassword) {
  $adminPassword = 'adminadmin'
}

# Login to get JWT token
Write-Host "  Logging in as $adminEmail..." -ForegroundColor Cyan
try {
  $loginPayload = @{
    email = $adminEmail
    password = $adminPassword
  } | ConvertTo-Json

  $loginResponse = Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/auth/login' -Body $loginPayload -ContentType 'application/json'
  $jwtToken = $loginResponse.access_token
  Write-Host '  [OK] JWT token obtained' -ForegroundColor Green
} catch {
  $errMsg = $_.Exception.Message
  Write-Host "ERROR: Failed to login and get JWT token: $errMsg" -ForegroundColor Red
  Write-Host '  Make sure BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD are set correctly in .env' -ForegroundColor Yellow
  exit 1
}

# ====== Step 10: Run dry-run discovery seed ======
Write-Host ''
Write-Host '[10/10] Running dry-run discovery seed...' -ForegroundColor Cyan
try {
  $seedPayload = @{
    entity_type = 'both'
    max_entities = 10
    dry_run = $true
  } | ConvertTo-Json

  $headers = @{
    'Authorization' = "Bearer $jwtToken"
    'Content-Type' = 'application/json'
  }

  $seedResponse = Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/discovery/seed' -Body $seedPayload -Headers $headers
  $taskId = $seedResponse.task_id
  Write-Host "  [OK] Discovery task started: $taskId" -ForegroundColor Green

  # Wait 10 seconds before checking status
  Write-Host '  Waiting 10 seconds for task to process...' -ForegroundColor Cyan
  Start-Sleep -Seconds 10

  # Check task status
  Write-Host '  Checking task status...' -ForegroundColor Cyan
  $statusResponse = Invoke-RestMethod -Method Get -Uri "http://localhost:8000/discovery/seed/$taskId" -Headers $headers
  
  Write-Host ''
  Write-Host '  Task Status:' -ForegroundColor Cyan
  $stateColor = 'Yellow'
  if ($statusResponse.state -eq 'SUCCESS') {
    $stateColor = 'Green'
  } elseif ($statusResponse.state -eq 'FAILURE') {
    $stateColor = 'Red'
  }
  Write-Host "    State: $($statusResponse.state)" -ForegroundColor $stateColor
  
  if ($statusResponse.result) {
    Write-Host '    Result:' -ForegroundColor Cyan
    $resultJson = $statusResponse.result | ConvertTo-Json -Compress
    Write-Host "      $resultJson" -ForegroundColor White
  }
  
  if ($statusResponse.error) {
    Write-Host "    Error: $($statusResponse.error)" -ForegroundColor Red
  }
  
  if ($statusResponse.info) {
    Write-Host '    Info:' -ForegroundColor Yellow
    $infoJson = $statusResponse.info | ConvertTo-Json -Compress
    Write-Host "      $infoJson" -ForegroundColor Yellow
  }

  # Determine if verification was successful
  if ($statusResponse.state -eq 'SUCCESS') {
    Write-Host ''
    Write-Host '  [OK] Perplexity integration verified successfully!' -ForegroundColor Green
  } elseif ($statusResponse.state -eq 'FAILURE') {
    Write-Host ''
    Write-Host '  [WARN] Task failed. Check the error above.' -ForegroundColor Yellow
  } else {
    Write-Host ''
    Write-Host "  [INFO] Task is still processing (state: $($statusResponse.state))" -ForegroundColor Yellow
    Write-Host "    Check status later: GET http://localhost:8000/discovery/seed/$taskId" -ForegroundColor Cyan
  }

} catch {
  $errMsg = $_.Exception.Message
  Write-Host "ERROR: Failed to run discovery seed: $errMsg" -ForegroundColor Red
  Write-Host '  This might indicate an issue with the Perplexity API key or service configuration.' -ForegroundColor Yellow
  exit 1
}

# ====== Print Summary with Next Steps ======
Write-Host ''
Write-Host '======================================' -ForegroundColor Cyan
Write-Host '  Perplexity Setup Complete!' -ForegroundColor Green
Write-Host '======================================' -ForegroundColor Cyan

Write-Host ''
Write-Host 'Next Steps:' -ForegroundColor Cyan
Write-Host '  1. Run a REAL discovery seed (not dry-run):' -ForegroundColor White
Write-Host '     POST http://localhost:8000/discovery/seed' -ForegroundColor Yellow
Write-Host '     Body: {"entity_type": "both", "max_entities": 100, "dry_run": false}' -ForegroundColor Yellow

Write-Host ''
Write-Host '  2. Refresh news data:' -ForegroundColor White
Write-Host '     POST http://localhost:8000/news/refresh' -ForegroundColor Yellow

Write-Host ''
Write-Host '  3. Access the application:' -ForegroundColor White
Write-Host '     Frontend: http://localhost:3000' -ForegroundColor Yellow
Write-Host '     API Docs: http://localhost:8000/docs' -ForegroundColor Yellow

Write-Host ''
Write-Host '  4. View logs:' -ForegroundColor White
Write-Host '     docker compose logs -f backend' -ForegroundColor Yellow
Write-Host '     docker compose logs -f worker' -ForegroundColor Yellow

Write-Host ''
Write-Host '  5. Check task status:' -ForegroundColor White
Write-Host "     GET http://localhost:8000/discovery/seed/$taskId" -ForegroundColor Yellow

Write-Host ''
Write-Host 'Login Credentials:' -ForegroundColor Cyan
Write-Host "  Email: $adminEmail" -ForegroundColor White
Write-Host "  Password: $adminPassword" -ForegroundColor White

Write-Host ''
