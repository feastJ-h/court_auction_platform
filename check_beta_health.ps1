param([string]$BaseUrl = "http://127.0.0.1:8000")
$ErrorActionPreference = "Stop"
$Failures = @()
foreach ($Endpoint in @("/health/live", "/health/ready", "/onbid")) {
    try {
        $Response = Invoke-WebRequest -UseBasicParsing -Uri "$($BaseUrl.TrimEnd('/'))$Endpoint" -TimeoutSec 10
        if ($Response.StatusCode -ne 200) { $Failures += "$Endpoint=$($Response.StatusCode)" }
    } catch { $Failures += "$Endpoint=unavailable" }
}
if ($Failures.Count) {
    $Message = "beta health FAILED: " + ($Failures -join ", ")
    Write-Error $Message
    exit 2
}
"beta health PASS"
