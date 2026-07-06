$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location $ProjectRoot
& $PythonExe -m uvicorn main_app:app --reload --host 127.0.0.1 --port 8000
