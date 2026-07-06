$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$StdoutPath = Join-Path $ProjectRoot "uvicorn.hidden.log"
$StderrPath = Join-Path $ProjectRoot "uvicorn.hidden.err.log"

$existing = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
    Select-Object -First 1 -ExpandProperty OwningProcess

if ($existing) {
    Write-Output "FastAPI already appears to be running on port 8000. PID: $existing"
    exit 0
}

$CmdExe = Join-Path $env:SystemRoot "System32\cmd.exe"
$Command = "cd /d `"$ProjectRoot`" && `"$PythonExe`" -m uvicorn main_app:app --host 127.0.0.1 --port 8000 1> `"$StdoutPath`" 2> `"$StderrPath`""

$process = Start-Process `
    -FilePath $CmdExe `
    -ArgumentList @("/c", $Command) `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden `
    -PassThru

Write-Output "FastAPI started on http://127.0.0.1:8000. PID: $($process.Id)"
