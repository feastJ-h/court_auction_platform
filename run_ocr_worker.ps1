param(
    [int]$Limit = 1,
    [switch]$Enqueue,
    [switch]$Mock,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location -LiteralPath $ProjectRoot

$argsList = @("-m", "backend.workers.ocr_worker", "--limit", "$Limit")
if ($Enqueue) {
    $argsList += "--enqueue"
}
if ($Mock) {
    $argsList += "--mock"
}
if ($DryRun) {
    $argsList += "--dry-run"
}

& $PythonExe @argsList
