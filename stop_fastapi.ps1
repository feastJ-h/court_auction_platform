$ErrorActionPreference = "Stop"

$processIds = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique

if (-not $processIds) {
    Write-Output "No FastAPI process found on port 8000."
    exit 0
}

foreach ($processId in $processIds) {
    Stop-Process -Id $processId -Force
    Write-Output "Stopped FastAPI process PID: $processId"
}
