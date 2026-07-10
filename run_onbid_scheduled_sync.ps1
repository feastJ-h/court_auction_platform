param(
    [ValidateSet("scheduled", "manual", "backfill")]
    [string]$RunType = "scheduled",
    [int]$Limit = 20,
    [int]$PageNo = 1,
    [int]$MaxPages = 1,
    [string]$MinDate = "2025-01-01",
    [string]$PrptDivCd = "0007,0005,0004,0002,0003,0006,0008,0011,0013",
    [ValidateSet("Y", "N")]
    [string]$PvctTrgtYn = "N",
    [string]$BidPrdYmdStart = "",
    [string]$BidPrdYmdEnd = "",
    [string]$MdfcnYmdStart = "",
    [string]$MdfcnYmdEnd = "",
    [string]$BidDivCd = "",
    [string]$DspsMthodCd = "",
    [ValidateSet("real_estate", "movable", "all", "notice", "national_property")]
    [string]$ApiKind = "all",
    [switch]$IncludeDetails,
    [int]$DetailLimit = 1,
    [switch]$IncludeNoticeDetails,
    [switch]$IncludeNoticeItems,
    [switch]$Sample
)

$ErrorActionPreference = "Stop"

if (-not $Sample) {
    if ($Limit -gt 50) { throw "Real ONBID sync is limited to Limit=50 in v009." }
    if ($MaxPages -gt 10) { throw "Real ONBID sync is limited to MaxPages=10 in v009." }
    if ($MinDate -ne "2025-01-01") { throw "Real ONBID sync requires MinDate=2025-01-01." }
    if ($DetailLimit -gt 20) { throw "Real ONBID detail enrichment is limited to 20 items per run in v009." }
}

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
        "--min-date", $MinDate,
        "--prpt-div-cd", $PrptDivCd,
        "--pvct-trgt-yn", $PvctTrgtYn,
        "--detail-limit", "$DetailLimit",
        "--run-type", $resolvedRunType,
        "--log-path", $LogPath
    )
    if ($BidPrdYmdStart) {
        $arguments += @("--bid-prd-ymd-start", $BidPrdYmdStart)
    }
    if ($BidPrdYmdEnd) {
        $arguments += @("--bid-prd-ymd-end", $BidPrdYmdEnd)
    }
    if ($MdfcnYmdStart) {
        $arguments += @("--mdfcn-ymd-start", $MdfcnYmdStart)
    }
    if ($MdfcnYmdEnd) {
        $arguments += @("--mdfcn-ymd-end", $MdfcnYmdEnd)
    }
    if ($BidDivCd) {
        $arguments += @("--bid-div-cd", $BidDivCd)
    }
    if ($DspsMthodCd) {
        $arguments += @("--dsps-mthod-cd", $DspsMthodCd)
    }
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

    "[$(Get-Date -Format o)] onbid scheduled sync start RunType=$RunType ResolvedRunType=$resolvedRunType Limit=$Limit PageNo=$PageNo MaxPages=$MaxPages MinDate=$MinDate ApiKind=$ApiKind PrptDivCd=$PrptDivCd PvctTrgtYn=$PvctTrgtYn BidPrdYmdStart=$BidPrdYmdStart BidPrdYmdEnd=$BidPrdYmdEnd IncludeDetails=$IncludeDetails DetailLimit=$DetailLimit IncludeNoticeDetails=$IncludeNoticeDetails IncludeNoticeItems=$IncludeNoticeItems Sample=$Sample" | Out-File -FilePath $LogPath -Encoding utf8
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
