param([Parameter(Mandatory=$true)][string]$BaseUrl)
$ErrorActionPreference = "Stop"
$BaseUrl = $BaseUrl.TrimEnd("/")
foreach ($Endpoint in @("/health/live", "/health/ready", "/health/version")) {
    1..3 | ForEach-Object {
        $Response = Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl$Endpoint" -TimeoutSec 15
        if ($Response.StatusCode -ne 200) { throw "$Endpoint attempt $_ failed: $($Response.StatusCode)" }
    }
}
foreach ($Category in @("all", "real_estate", "movable", "national_property")) {
    $Query = if ($Category -eq "all") { "sort=closing_soon" } else { "sort=closing_soon&category=$Category" }
    $Response = Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/onbid?$Query" -TimeoutSec 30
    if ($Response.StatusCode -ne 200) { throw "category $Category returned $($Response.StatusCode)" }
    if ($Response.Content -notmatch "data-active-category=`"$Category`"") { throw "category $Category active marker mismatch" }
    $Matches = [regex]::Matches($Response.Content, 'data-item-category="([^"]+)"')
    if ($Category -ne "all" -and ($Matches | Where-Object { $_.Groups[1].Value -ne $Category })) { throw "category $Category leaked another category" }
}
"external beta E2E PASS: $BaseUrl"
