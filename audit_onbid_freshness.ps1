param(
    [string]$MinDate = "2025-01-01"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
Set-Location $ProjectRoot

& $PythonExe -m backend.workers.onbid_maintenance audit-freshness --min-date $MinDate
exit $LASTEXITCODE
