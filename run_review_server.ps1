param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
Set-Location $ProjectRoot

$env:REVIEW_MODE = "true"
Write-Output "Review server starting on http://127.0.0.1:$Port with REVIEW_MODE=true. Start tunnels manually only after safety checklist review."
& $PythonExe -m uvicorn main_app:app --host 127.0.0.1 --port $Port
