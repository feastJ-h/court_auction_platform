$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Runtime = Join-Path $Root "storage\runtime"
$Rows = foreach ($Name in @("beta-app", "beta-tunnel")) {
    $Path = Join-Path $Runtime "$Name.pid"
    $PidValue = if (Test-Path -LiteralPath $Path) { Get-Content -LiteralPath $Path } else { $null }
    $Process = if ($PidValue) { Get-Process -Id $PidValue -ErrorAction SilentlyContinue } else { $null }
    [ordered]@{ name = $Name; pid = $PidValue; running = [bool]$Process }
}
$Rows | ConvertTo-Json -Compress
