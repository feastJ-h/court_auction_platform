param(
    [string]$Endpoint = "ws://127.0.0.1:4500",
    [int]$Limit = 1,
    [int]$TimeoutSeconds = 900,
    [int]$IdleSleepSeconds = 10,
    [string]$Model = "",
    [switch]$Mock
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

while ($true) {
    try {
        $arguments = @{
            Endpoint = $Endpoint
            Limit = $Limit
            TimeoutSeconds = $TimeoutSeconds
        }
        if ($Model) {
            $arguments["Model"] = $Model
        }
        if ($Mock) {
            $arguments["Mock"] = $true
        }
        & .\run_codex_app_server_worker.ps1 @arguments
    } catch {
        Write-Output "app-server worker loop error: $($_.Exception.Message)"
    }
    Start-Sleep -Seconds $IdleSleepSeconds
}
