param(
    [ValidateSet("scheduled", "manual", "backfill", "retry_failed")]
    [string]$RunType = "scheduled",
    [int]$Limit = 40,
    [int]$MaxPages = 8,
    [int]$DaysBack = 7,
    [string]$StartDate = "",
    [string]$EndDate = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$LogDir = Join-Path $ProjectRoot "storage\logs\crawl_runs"
$LockPath = Join-Path $ProjectRoot "storage\scheduled_crawl.lock"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $LockPath) | Out-Null

$lockStream = $null
try {
    $lockStream = [System.IO.File]::Open($LockPath, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
} catch {
    Write-Output "Another scheduled crawl appears to be running. Lock: $LockPath"
    exit 2
}

try {
    Set-Location $ProjectRoot
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $LogPath = Join-Path $LogDir "crawl_$($RunType)_$timestamp.log"

    $arguments = @(
        "-m", "backend.workers.scheduled_crawl",
        "--run-type", $RunType,
        "--limit", "$Limit",
        "--max-pages", "$MaxPages",
        "--days-back", "$DaysBack",
        "--log-path", $LogPath
    )
    if ($StartDate) {
        $arguments += @("--start-date", $StartDate)
    }
    if ($EndDate) {
        $arguments += @("--end-date", $EndDate)
    }
    if ($DryRun) {
        $arguments += "--dry-run"
    }

    "[$(Get-Date -Format o)] scheduled crawl start RunType=$RunType Limit=$Limit MaxPages=$MaxPages DaysBack=$DaysBack DryRun=$DryRun" | Out-File -FilePath $LogPath -Encoding utf8
    $processOutput = & $PythonExe @arguments 2>&1
    $exitCode = $LASTEXITCODE
    $processOutput | Out-File -FilePath $LogPath -Append -Encoding utf8
    "[$(Get-Date -Format o)] scheduled crawl finished ExitCode=$exitCode" | Out-File -FilePath $LogPath -Append -Encoding utf8
    Write-Output "Scheduled crawl finished. ExitCode=$exitCode Log=$LogPath"
    exit $exitCode
} finally {
    if ($lockStream) {
        $lockStream.Dispose()
    }
}
