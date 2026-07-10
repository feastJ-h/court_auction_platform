$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Runtime = Join-Path $Root "storage\runtime"
foreach ($Name in @("beta-tunnel.pid", "beta-app.pid")) {
    $Path = Join-Path $Runtime $Name
    if (-not (Test-Path -LiteralPath $Path)) { continue }
    $PidValue = (Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue | Select-Object -First 1)
    if (-not $PidValue) { Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue; continue }
    $Process = Get-Process -Id $PidValue -ErrorAction SilentlyContinue
    if ($Process) { Stop-Process -Id $Process.Id -Force }
    Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
}
"beta review processes stopped"
