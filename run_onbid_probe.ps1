param(
    [ValidateSet("real_estate", "movable", "notice", "national_property")]
    [string]$ApiKind = "national_property",
    [int]$Limit = 20,
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
    [switch]$IncludeDetails,
    [int]$DetailLimit = 1,
    [switch]$Sample
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location $ProjectRoot

if (-not $Sample) {
    if ($Limit -gt 20) { throw "Real ONBID probe is limited to Limit=20 in v005." }
    if ($MaxPages -gt 1) { throw "Real ONBID probe is limited to MaxPages=1 in v005." }
    if ($MinDate -ne "2025-01-01") { throw "Real ONBID probe requires MinDate=2025-01-01 in v005." }
    if ($DetailLimit -gt 1) { throw "Real ONBID probe is limited to DetailLimit=1 in v006-a2." }
}

$arguments = @(
    "-m", "backend.workers.onbid_sync",
    "--limit", "$Limit",
    "--max-pages", "$MaxPages",
    "--api-kind", $ApiKind,
    "--min-date", $MinDate,
    "--run-type", "onbid_probe",
    "--prpt-div-cd", $PrptDivCd,
    "--pvct-trgt-yn", $PvctTrgtYn,
    "--detail-limit", "$DetailLimit"
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

if ($IncludeDetails -and $ApiKind -in @("real_estate", "movable")) {
    $arguments += "--include-details"
}
if ($ApiKind -eq "notice") {
    $arguments += @("--include-notice-details", "--include-notice-items")
}
if ($Sample) {
    $arguments += "--sample"
}

Write-Output "ONBID probe start ApiKind=$ApiKind Limit=$Limit MaxPages=$MaxPages MinDate=$MinDate PrptDivCd=$PrptDivCd PvctTrgtYn=$PvctTrgtYn BidPrdYmdStart=$BidPrdYmdStart BidPrdYmdEnd=$BidPrdYmdEnd IncludeDetails=$IncludeDetails DetailLimit=$DetailLimit Sample=$Sample"
& $PythonExe @arguments
exit $LASTEXITCODE
