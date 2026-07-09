param(
    [ValidateSet("real_estate", "movable", "notice", "national_property")]
    [string]$ApiKind = "real_estate",
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
    [switch]$IncludeDetails,
    [int]$DetailLimit = 1,
    [switch]$Sample
)

$ErrorActionPreference = "Stop"

if (-not $Sample) {
    if ($Limit -gt 20) { throw "Fresh probe is limited to Limit=20." }
    if ($MaxPages -gt 1) { throw "Fresh probe is limited to MaxPages=1." }
    if ($MinDate -ne "2025-01-01") { throw "Fresh probe requires MinDate=2025-01-01." }
    if ($DetailLimit -gt 1) { throw "Fresh probe is limited to DetailLimit=1." }
}

$args = @(
    "-ExecutionPolicy", "Bypass",
    "-File", ".\run_onbid_probe.ps1",
    "-ApiKind", $ApiKind,
    "-Limit", "$Limit",
    "-PageNo", "$PageNo",
    "-MaxPages", "$MaxPages",
    "-MinDate", $MinDate,
    "-PrptDivCd", $PrptDivCd,
    "-PvctTrgtYn", $PvctTrgtYn,
    "-BidPrdYmdStart", $BidPrdYmdStart,
    "-BidPrdYmdEnd", $BidPrdYmdEnd,
    "-DetailLimit", "$DetailLimit"
)
if ($MdfcnYmdStart) {
    $args += @("-MdfcnYmdStart", $MdfcnYmdStart)
}
if ($MdfcnYmdEnd) {
    $args += @("-MdfcnYmdEnd", $MdfcnYmdEnd)
}
if ($IncludeDetails) {
    $args += "-IncludeDetails"
}
if ($Sample) {
    $args += "-Sample"
}

powershell @args
exit $LASTEXITCODE
