param(
    [int]$Limit = 50,
    [int]$MaxPages = 15
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location $ProjectRoot

& $PythonExe -c "import asyncio; from orchestrator import run_since_2026_06_15_collection; result = asyncio.run(run_since_2026_06_15_collection(max_items=$Limit, max_pages=$MaxPages)); print(result); print('Report: reports/collection_since_2026_06_15_report.md')"
