param(
    [ValidateSet("real_estate", "movable", "notice", "national_property")]
    [string]$ApiKind = "real_estate",
    [int]$Limit = 20,
    [int]$MaxPages = 1,
    [string]$MinDate = "2025-01-01",
    [switch]$Sample
)

$ErrorActionPreference = "Stop"

if (-not $Sample) {
    if ($Limit -gt 20) { throw "Fresh probe is limited to Limit=20." }
    if ($MaxPages -gt 1) { throw "Fresh probe is limited to MaxPages=1." }
    if ($MinDate -ne "2025-01-01") { throw "Fresh probe requires MinDate=2025-01-01." }
}

$args = @(
    "-ExecutionPolicy", "Bypass",
    "-File", ".\run_onbid_probe.ps1",
    "-ApiKind", $ApiKind,
    "-Limit", "$Limit",
    "-MaxPages", "$MaxPages",
    "-MinDate", $MinDate
)
if ($Sample) {
    $args += "-Sample"
}

powershell @args
exit $LASTEXITCODE
