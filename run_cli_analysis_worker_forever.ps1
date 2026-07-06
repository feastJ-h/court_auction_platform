param(
    [int]$Limit = 1,
    [int]$TimeoutSeconds = 900,
    [int]$IdleSleepSeconds = 10,
    [string]$CodexCommand = "codex",
    [switch]$Mock
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

while ($true) {
    try {
        $arguments = @(
            "-Limit", $Limit,
            "-TimeoutSeconds", $TimeoutSeconds,
            "-CodexCommand", $CodexCommand
        )
        if ($Mock) {
            $arguments += "-Mock"
        }
        & .\run_cli_analysis_worker.ps1 @arguments
    } catch {
        Write-Output "exec worker loop error: $($_.Exception.Message)"
    }
    Start-Sleep -Seconds $IdleSleepSeconds
}
