[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$ComposeFile = Join-Path $RepoRoot "infra\docker\docker-compose.yml"
$EnvFile = Join-Path $RepoRoot "infra\docker\.env"
$EnvExampleFile = Join-Path $RepoRoot "infra\docker\.env.example"

function Stop-WithMessage {
    param([string]$Message)

    Write-Host "[FAIL] $Message" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $ComposeFile)) {
    Stop-WithMessage "Compose file not found: $ComposeFile"
}

if (-not (Test-Path -LiteralPath $EnvFile)) {
    Stop-WithMessage "Env file not found: $EnvFile. Create it from $EnvExampleFile first."
}

Push-Location $RepoRoot
try {
    Write-Host "[INFO] Stopping CasinoKing local stack..." -ForegroundColor Cyan
    docker compose -f $ComposeFile --env-file $EnvFile down
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "docker compose down failed with exit code $LASTEXITCODE"
    }

    Write-Host "[PASS] CasinoKing local stack stopped." -ForegroundColor Green
}
finally {
    Pop-Location
}
