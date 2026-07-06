param(
    [int]$Limit = 1,
    [int]$TimeoutSeconds = 900,
    [string]$CodexCommand = "codex",
    [switch]$Mock
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location $ProjectRoot

$arguments = @(
    "-m",
    "backend.analysis_worker.cli_worker",
    "--limit",
    $Limit,
    "--timeout",
    $TimeoutSeconds,
    "--codex-command",
    $CodexCommand
)

if ($Mock) {
    $arguments += "--mock"
}

& $PythonExe @arguments
