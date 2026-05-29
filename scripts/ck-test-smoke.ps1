[CmdletBinding()]
param(
    [string[]]$PytestTarget = @("tests/integration/test_frontend_smoke.py")
)

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

function Convert-ToWorkspacePath {
    param([string]$Path)

    if ($Path -like "/workspace/*") {
        return $Path
    }

    $normalized = $Path.Replace("\", "/").TrimStart(".", "/")
    return "/workspace/$normalized"
}

if (-not (Test-Path -LiteralPath $ComposeFile)) {
    Stop-WithMessage "Compose file not found: $ComposeFile"
}

if (-not (Test-Path -LiteralPath $EnvFile)) {
    Stop-WithMessage "Env file not found: $EnvFile. Create it from $EnvExampleFile first."
}

$WorkspaceTargets = @($PytestTarget | ForEach-Object { Convert-ToWorkspacePath -Path $_ })
$DockerVolume = "${RepoRoot}:/workspace"

Push-Location $RepoRoot
try {
    Write-Host "[INFO] Canonical smoke suite target(s): $($WorkspaceTargets -join ', ')" -ForegroundColor Cyan
    Write-Host "[INFO] Running pytest from the backend image on Docker network casinoking_default." -ForegroundColor Cyan

    $dockerArgs = @(
        "run",
        "--rm",
        "--network",
        "casinoking_default",
        "-v",
        $DockerVolume,
        "-w",
        "/workspace/backend",
        "-e",
        "CASINOKING_API_BASE_URL=http://backend:8000/api/v1",
        "-e",
        "CASINOKING_FRONTEND_BASE_URL=http://edge",
        "-e",
        "CASINOKING_PUBLIC_EDGE_BASE_URL=http://edge",
        "-e",
        "CASINOKING_V1_FRONTEND_BASE_URL=http://frontend:3000",
        "-e",
        "CASINOKING_SITE_V3_FRONTEND_BASE_URL=http://frontend-v3:3001",
        "-e",
        "CASINOKING_PUBLIC_V1_BASE_URL=http://localhost:3000",
        "-e",
        "CASINOKING_PUBLIC_SITE_V3_BASE_URL=http://localhost:3000",
        "-e",
        "CASINOKING_TEST_DATABASE_URL=postgresql://casinoking:casinoking@postgres:5432/casinoking",
        "-e",
        "CASINOKING_SITE_ACCESS_PASSWORD=change-me",
        "casinoking-backend",
        "python",
        "-m",
        "pytest"
    ) + $WorkspaceTargets + @("-q")

    & docker @dockerArgs

    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "canonical pytest smoke suite failed with exit code $LASTEXITCODE"
    }

    Write-Host "[PASS] canonical pytest smoke suite completed." -ForegroundColor Green
}
finally {
    Pop-Location
}
