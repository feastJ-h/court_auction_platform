param(
    [switch]$DryRun = $true,
    [switch]$Apply,
    [string]$MinDate = "2025-01-01"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
Set-Location $ProjectRoot

$mode = if ($Apply) { "apply-derived-fields" } else { "dry-run-derived-fields" }
& $PythonExe -m backend.workers.onbid_maintenance $mode --min-date $MinDate
exit $LASTEXITCODE
