param(
    [int]$Limit = 100
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location $ProjectRoot

& $PythonExe -c "from orchestrator import ingest_local_quarantine_files; result = ingest_local_quarantine_files(max_items=$Limit); print(result); print('Report: reports/local_quarantine_ingest_report.md')"
