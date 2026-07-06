param(
    [string]$Endpoint = "ws://127.0.0.1:4500",
    [int]$Limit = 1,
    [int]$TimeoutSeconds = 900,
    [string]$Model = "",
    [switch]$Mock
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location $ProjectRoot

$arguments = @(
    "-m",
    "backend.analysis_worker.app_server_worker",
    "--endpoint",
    $Endpoint,
    "--limit",
    $Limit,
    "--timeout",
    $TimeoutSeconds
)

if ($Model) {
    $arguments += @("--model", $Model)
}

if ($Mock) {
    $arguments += "--mock"
}

& $PythonExe @arguments
