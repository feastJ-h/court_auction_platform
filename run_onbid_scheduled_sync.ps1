param(
    [ValidateSet("scheduled", "manual", "backfill")]
    [string]$RunType = "scheduled",
    [int]$Limit = 100,
    [int]$PageNo = 1,
    [int]$MaxPages = 8,
    [ValidateSet("real_estate", "movable", "all", "notice", "national_property")]
    [string]$ApiKind = "all",
    [switch]$IncludeDetails,
    [switch]$IncludeNoticeDetails,
    [switch]$IncludeNoticeItems,
    [switch]$Sample
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$LogDir = Join-Path $ProjectRoot "storage\logs\onbid"
$LockPath = Join-Path $ProjectRoot "storage\onbid_scheduled_sync.lock"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $LockPath) | Out-Null

$lockStream = $null
try {
    $lockStream = [System.IO.File]::Open($LockPath, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
} catch {
    Write-Output "Another ONBID scheduled sync appears to be running. Lock: $LockPath"
    exit 2
}

try {
    Set-Location $ProjectRoot
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $LogPath = Join-Path $LogDir "onbid_$($RunType)_$timestamp.log"
    $resolvedRunType = if ($Sample) { "onbid_sample" } elseif ($RunType -eq "scheduled") { "onbid_scheduled" } elseif ($RunType -eq "backfill") { "onbid_backfill" } else { "onbid_manual" }

    $arguments = @(
        "-m", "backend.workers.onbid_sync",
        "--limit", "$Limit",
        "--page-no", "$PageNo",
        "--max-pages", "$MaxPages",
        "--api-kind", $ApiKind,
        "--run-type", $resolvedRunType,
        "--log-path", $LogPath
    )
    if ($IncludeDetails) {
        $arguments += "--include-details"
    }
    if ($IncludeNoticeDetails) {
        $arguments += "--include-notice-details"
    }
    if ($IncludeNoticeItems) {
        $arguments += "--include-notice-items"
    }
    if ($Sample) {
        $arguments += "--sample"
    }

    "[$(Get-Date -Format o)] onbid scheduled sync start RunType=$RunType ResolvedRunType=$resolvedRunType Limit=$Limit PageNo=$PageNo MaxPages=$MaxPages ApiKind=$ApiKind IncludeDetails=$IncludeDetails IncludeNoticeDetails=$IncludeNoticeDetails IncludeNoticeItems=$IncludeNoticeItems Sample=$Sample" | Out-File -FilePath $LogPath -Encoding utf8
    $processOutput = & $PythonExe @arguments 2>&1
    $exitCode = $LASTEXITCODE
    $processOutput | Out-File -FilePath $LogPath -Append -Encoding utf8
    "[$(Get-Date -Format o)] onbid scheduled sync finished ExitCode=$exitCode" | Out-File -FilePath $LogPath -Append -Encoding utf8
    Write-Output "ONBID scheduled sync finished. ExitCode=$exitCode Log=$LogPath"
    exit $exitCode
} finally {
    if ($lockStream) {
        $lockStream.Dispose()
    }
}
