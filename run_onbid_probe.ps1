param(
    [ValidateSet("real_estate", "movable", "notice", "national_property")]
    [string]$ApiKind = "national_property",
    [int]$Limit = 20,
    [int]$MaxPages = 1,
    [switch]$Sample
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location $ProjectRoot

$arguments = @(
    "-m", "backend.workers.onbid_sync",
    "--limit", "$Limit",
    "--max-pages", "$MaxPages",
    "--api-kind", $ApiKind,
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

Write-Output "ONBID probe start ApiKind=$ApiKind Limit=$Limit MaxPages=$MaxPages Sample=$Sample"
& $PythonExe @arguments
exit $LASTEXITCODE
