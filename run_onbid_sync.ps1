param(
    [int]$Limit = 20,
    [int]$PageNo = 1,
    [int]$MaxPages = 1,
    [string]$PrptDivCd = "0007,0010,0005,0002,0003,0006,0008,0011,0013",
    [string]$PvctTrgtYn = "N",
    [ValidateSet("real_estate", "movable", "all", "notice")]
    [string]$ApiKind = "real_estate",
    [switch]$IncludeDetails,
    [switch]$IncludeNoticeDetails,
    [switch]$IncludeNoticeItems,
    [string]$RunType = "",
    [switch]$Sample
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$LogDir = Join-Path $ProjectRoot "storage\logs\onbid"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Set-Location $ProjectRoot
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $LogDir "onbid_sync_$timestamp.log"

$arguments = @(
    "-m", "backend.workers.onbid_sync",
    "--limit", "$Limit",
    "--page-no", "$PageNo",
    "--max-pages", "$MaxPages",
    "--prpt-div-cd", $PrptDivCd,
    "--pvct-trgt-yn", $PvctTrgtYn,
    "--api-kind", $ApiKind,
    "--log-path", $LogPath
)
if ($RunType) {
    $arguments += @("--run-type", $RunType)
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

"[$(Get-Date -Format o)] onbid sync start Limit=$Limit PageNo=$PageNo MaxPages=$MaxPages ApiKind=$ApiKind IncludeDetails=$IncludeDetails IncludeNoticeDetails=$IncludeNoticeDetails IncludeNoticeItems=$IncludeNoticeItems Sample=$Sample RunType=$RunType" | Out-File -FilePath $LogPath -Encoding utf8
$processOutput = & $PythonExe @arguments 2>&1
$exitCode = $LASTEXITCODE
$processOutput | Out-File -FilePath $LogPath -Append -Encoding utf8
"[$(Get-Date -Format o)] onbid sync finished ExitCode=$exitCode" | Out-File -FilePath $LogPath -Append -Encoding utf8
Write-Output "ONBID sync finished. ExitCode=$exitCode Log=$LogPath"
exit $exitCode
