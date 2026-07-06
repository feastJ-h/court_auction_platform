param(
    [ValidateSet("real_estate", "movable", "notice", "national_property")]
    [string]$ApiKind = "national_property",
    [int]$Limit = 20,
    [int]$MaxPages = 1,
    [string]$MinDate = "2025-01-01",
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
}

$arguments = @(
    "-m", "backend.workers.onbid_sync",
    "--limit", "$Limit",
    "--max-pages", "$MaxPages",
    "--api-kind", $ApiKind,
    "--min-date", $MinDate,
    "--run-type", "onbid_probe"
)

if ($ApiKind -in @("real_estate", "movable")) {
    $arguments += "--include-details"
}
if ($ApiKind -eq "notice") {
    $arguments += @("--include-notice-details", "--include-notice-items")
}
if ($Sample) {
    $arguments += "--sample"
}

Write-Output "ONBID probe start ApiKind=$ApiKind Limit=$Limit MaxPages=$MaxPages MinDate=$MinDate Sample=$Sample"
& $PythonExe @arguments
exit $LASTEXITCODE
