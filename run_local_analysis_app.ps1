param(
    [string]$Endpoint = "ws://127.0.0.1:4500",
    [int]$Limit = 1,
    [int]$TimeoutSeconds = 900,
    [int]$IdleSleepSeconds = 10,
    [string]$Model = "",
    [switch]$Mock,
    [switch]$RunOnce
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Resolve-CodexExecutable {
    $localCodexRoot = Join-Path $env:LOCALAPPDATA "OpenAI\Codex\bin"
    if (Test-Path $localCodexRoot) {
        $localCodex = Get-ChildItem -Path $localCodexRoot -Recurse -Filter "codex.exe" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($localCodex -and (Test-Path $localCodex.FullName)) {
            return $localCodex.FullName
        }
    }

    $commands = @(Get-Command codex -All -ErrorAction SilentlyContinue)
    foreach ($command in $commands) {
        $candidate = $command.Source
        if (-not $candidate) {
            $candidate = $command.Path
        }
        if ($candidate -and $candidate.ToLowerInvariant().EndsWith(".exe") -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    foreach ($command in $commands) {
        $candidate = $command.Source
        if (-not $candidate) {
            $candidate = $command.Path
        }
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    throw "Codex executable was not found. Run 'codex --version' in PowerShell and confirm Codex CLI is installed."
}

function Test-EndpointListening {
    param([string]$EndpointValue)

    try {
        $uri = [Uri]$EndpointValue
        $readyUrl = "http://$($uri.Host):$($uri.Port)/readyz"
        $response = Invoke-WebRequest -Uri $readyUrl -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        return ($response.StatusCode -eq 200)
    } catch {
        return $false
    }
}

$appServer = $null
$startedAppServer = $false

if ($Mock) {
    Write-Output "Mock mode: Codex app-server will not be started."
} elseif (Test-EndpointListening -EndpointValue $Endpoint) {
    Write-Output "Existing Codex app-server detected at $Endpoint. Reusing it."
} else {
    $stdoutPath = Join-Path $ProjectRoot "codex_app_server.stdout.log"
    $stderrPath = Join-Path $ProjectRoot "codex_app_server.stderr.log"
    $codexExe = Resolve-CodexExecutable
    $powershellExe = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    $appServerCommand = @"
Set-Location -LiteralPath '$ProjectRoot'
& '$codexExe' app-server --listen '$Endpoint' *> '$stdoutPath'
"@
    $encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($appServerCommand))
    $appServer = Start-Process `
        -FilePath $powershellExe `
        -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", $encodedCommand) `
        -WorkingDirectory $ProjectRoot `
        -WindowStyle Hidden `
        -PassThru
    $startedAppServer = $true
    Write-Output "Starting Codex app-server at $Endpoint. PID: $($appServer.Id)"
    Write-Output "Codex executable: $codexExe"
    Start-Sleep -Seconds 5

    if ($appServer.HasExited -or -not (Test-EndpointListening -EndpointValue $Endpoint)) {
        Write-Output "Codex app-server did not become ready. Check:"
        Write-Output "  $stdoutPath"
        Write-Output "  $stderrPath"
        throw "Codex app-server failed to start."
    }
}

Write-Output "Starting local analysis worker loop. Press Ctrl+C to stop the worker."

try {
    $workerParams = @{
        Endpoint = $Endpoint
        Limit = $Limit
        TimeoutSeconds = $TimeoutSeconds
    }
    if ($Model) {
        $workerParams["Model"] = $Model
    }
    if ($Mock) {
        $workerParams["Mock"] = $true
    }
    if ($RunOnce) {
        & .\run_codex_app_server_worker.ps1 @workerParams
    } else {
        $workerParams["IdleSleepSeconds"] = $IdleSleepSeconds
        & .\run_codex_app_server_worker_forever.ps1 @workerParams
    }
}
finally {
    if ($startedAppServer -and $appServer -and -not $appServer.HasExited) {
        Stop-Process -Id $appServer.Id -Force
        Write-Output "Stopped Codex app-server launcher PID: $($appServer.Id)"
    }
}
