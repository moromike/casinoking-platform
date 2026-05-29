[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$ComposeFile = Join-Path $RepoRoot "infra\docker\docker-compose.yml"
$EnvFile = Join-Path $RepoRoot "infra\docker\.env"
$EnvExampleFile = Join-Path $RepoRoot "infra\docker\.env.example"

Add-Type -AssemblyName System.Net.Http

$script:Failures = 0

function Write-Pass {
    param(
        [string]$Name,
        [string]$Detail
    )

    Write-Host ("[PASS] {0} - {1}" -f $Name, $Detail) -ForegroundColor Green
}

function Write-Fail {
    param(
        [string]$Name,
        [string]$Detail
    )

    $script:Failures += 1
    Write-Host ("[FAIL] {0} - {1}" -f $Name, $Detail) -ForegroundColor Red
}

function Invoke-DoctorCheck {
    param(
        [string]$Name,
        [scriptblock]$Check
    )

    try {
        $detail = & $Check
        Write-Pass -Name $Name -Detail ([string]$detail)
    }
    catch {
        Write-Fail -Name $Name -Detail $_.Exception.Message
    }
}

function Assert-LastExitCode {
    param(
        [string]$CommandName,
        [object[]]$Output
    )

    if ($LASTEXITCODE -ne 0) {
        throw ("{0} failed with exit code {1}: {2}" -f $CommandName, $LASTEXITCODE, (($Output | Out-String).Trim()))
    }
}

function Get-EnvValue {
    param(
        [string]$Name,
        [string]$DefaultValue
    )

    if (-not (Test-Path -LiteralPath $EnvFile)) {
        return $DefaultValue
    }

    $line = Get-Content -LiteralPath $EnvFile |
        Where-Object { $_ -match "^\s*$([regex]::Escape($Name))\s*=" } |
        Select-Object -Last 1

    if (-not $line) {
        return $DefaultValue
    }

    $value = $line -replace "^\s*$([regex]::Escape($Name))\s*=", ""
    return $value.Trim().Trim('"').Trim("'")
}

function Convert-ComposeJson {
    param([object[]]$RawOutput)

    $text = ($RawOutput | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($text)) {
        return @()
    }

    try {
        return @($text | ConvertFrom-Json)
    }
    catch {
        $items = @()
        foreach ($line in $RawOutput) {
            $trimmed = ([string]$line).Trim()
            if ([string]::IsNullOrWhiteSpace($trimmed)) {
                continue
            }
            $items += ($trimmed | ConvertFrom-Json)
        }
        return $items
    }
}

function Test-Http200 {
    param([string]$Uri)

    $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -ne 200) {
        throw ("Expected HTTP 200 from {0}, got {1}" -f $Uri, $response.StatusCode)
    }
    return ("HTTP {0} from {1}" -f $response.StatusCode, $Uri)
}

function Test-HttpRedirect {
    param(
        [string]$Uri,
        [string]$ExpectedLocation
    )

    $handler = [System.Net.Http.HttpClientHandler]::new()
    $handler.AllowAutoRedirect = $false
    $client = [System.Net.Http.HttpClient]::new($handler)

    try {
        $response = $client.GetAsync($Uri).GetAwaiter().GetResult()
        $statusCode = [int]$response.StatusCode
        if ($statusCode -notin @(307, 308)) {
            throw ("Expected HTTP 307/308 from {0}, got {1}" -f $Uri, $statusCode)
        }

        $location = [string]$response.Headers.Location
        if ($location -ne $ExpectedLocation) {
            throw ("Expected redirect from {0} to {1}, got {2}" -f $Uri, $ExpectedLocation, $location)
        }

        return ("HTTP {0} redirect from {1} to {2}" -f $statusCode, $Uri, $location)
    }
    finally {
        $client.Dispose()
        $handler.Dispose()
    }
}

Write-Host "CasinoKing local doctor" -ForegroundColor Cyan
Write-Host ("Repo root: {0}" -f $RepoRoot) -ForegroundColor DarkCyan

Invoke-DoctorCheck -Name "Compose file" -Check {
    if (-not (Test-Path -LiteralPath $ComposeFile)) {
        throw "Not found: $ComposeFile"
    }
    return $ComposeFile
}

Invoke-DoctorCheck -Name "Env file" -Check {
    if (-not (Test-Path -LiteralPath $EnvFile)) {
        throw "Not found: $EnvFile. Create it from $EnvExampleFile first."
    }
    return $EnvFile
}

Invoke-DoctorCheck -Name "Docker daemon" -Check {
    $output = docker info --format "{{.ServerVersion}}" 2>&1
    Assert-LastExitCode -CommandName "docker info" -Output $output
    return ("daemon reachable, server {0}" -f (($output | Out-String).Trim()))
}

Invoke-DoctorCheck -Name "Compose services healthy" -Check {
    if (-not (Test-Path -LiteralPath $EnvFile)) {
        throw "Env file missing; cannot inspect compose services."
    }

    $raw = docker compose -f $ComposeFile --env-file $EnvFile ps --format json 2>&1
    Assert-LastExitCode -CommandName "docker compose ps" -Output $raw

    $services = @(Convert-ComposeJson -RawOutput $raw)
    $expectedServices = @("backend", "frontend", "frontend-v3", "edge", "postgres", "redis")
    $statusLines = @()

    foreach ($serviceName in $expectedServices) {
        $service = $services | Where-Object { $_.Service -eq $serviceName } | Select-Object -First 1
        if (-not $service) {
            throw "Missing compose service: $serviceName"
        }

        $state = [string]$service.State
        $health = [string]$service.Health
        if ($state -ne "running") {
            throw ("Service {0} is {1}, expected running." -f $serviceName, $state)
        }
        if ($health -ne "healthy") {
            throw ("Service {0} health is '{1}', expected healthy." -f $serviceName, $health)
        }

        $statusLines += ("{0}=running/healthy" -f $serviceName)
    }

    return ($statusLines -join "; ")
}

Invoke-DoctorCheck -Name "Public edge HTTP" -Check {
    $edgePort = Get-EnvValue -Name "EDGE_PORT" -DefaultValue "3000"
    return Test-Http200 -Uri "http://localhost:$edgePort"
}

Invoke-DoctorCheck -Name "Public edge Site V3 marker" -Check {
    $edgePort = Get-EnvValue -Name "EDGE_PORT" -DefaultValue "3000"
    $uri = "http://localhost:$edgePort"
    $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 10
    if ($response.Content -notlike "*site-v3-page*") {
        throw "Expected Site V3 markup at $uri"
    }
    return "Site V3 markup served from $uri"
}

Invoke-DoctorCheck -Name "V1 frontend root redirect" -Check {
    $frontendPort = Get-EnvValue -Name "FRONTEND_PORT" -DefaultValue "3002"
    return Test-HttpRedirect -Uri "http://localhost:$frontendPort" -ExpectedLocation "/admin"
}

Invoke-DoctorCheck -Name "V1 frontend admin redirect" -Check {
    $frontendPort = Get-EnvValue -Name "FRONTEND_PORT" -DefaultValue "3002"
    $edgePort = Get-EnvValue -Name "EDGE_PORT" -DefaultValue "3000"
    return Test-HttpRedirect -Uri "http://localhost:$frontendPort/admin" -ExpectedLocation "http://localhost:$edgePort/admin"
}

Invoke-DoctorCheck -Name "Site V3 frontend direct HTTP" -Check {
    $frontendV3Port = Get-EnvValue -Name "FRONTEND_V3_PORT" -DefaultValue "3001"
    return Test-Http200 -Uri "http://localhost:$frontendV3Port"
}

Invoke-DoctorCheck -Name "Backend live health" -Check {
    return Test-Http200 -Uri "http://localhost:8000/api/v1/health/live"
}

Invoke-DoctorCheck -Name "Postgres query" -Check {
    if (-not (Test-Path -LiteralPath $EnvFile)) {
        throw "Env file missing; cannot run Postgres query."
    }

    $postgresUser = Get-EnvValue -Name "POSTGRES_USER" -DefaultValue "casinoking"
    $postgresDb = Get-EnvValue -Name "POSTGRES_DB" -DefaultValue "casinoking"
    $query = "select now() as server_time, current_database() as db, current_user as db_user;"

    $output = docker compose -f $ComposeFile --env-file $EnvFile exec -T postgres psql -U $postgresUser -d $postgresDb -At -c $query 2>&1
    Assert-LastExitCode -CommandName "postgres query" -Output $output

    return ("query ok: {0}" -f (($output | Out-String).Trim()))
}

Invoke-DoctorCheck -Name "Redis ping" -Check {
    if (-not (Test-Path -LiteralPath $EnvFile)) {
        throw "Env file missing; cannot ping Redis."
    }

    $output = docker compose -f $ComposeFile --env-file $EnvFile exec -T redis redis-cli ping 2>&1
    Assert-LastExitCode -CommandName "redis ping" -Output $output

    $text = ($output | Out-String).Trim()
    if ($text -ne "PONG") {
        throw "Expected PONG, got: $text"
    }

    return $text
}

if ($script:Failures -gt 0) {
    Write-Host ("Doctor completed with {0} failing check(s)." -f $script:Failures) -ForegroundColor Red
    exit 1
}

Write-Host "Doctor completed successfully. All checks passed." -ForegroundColor Green
exit 0
