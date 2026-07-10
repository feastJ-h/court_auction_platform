param(
    [int]$Port = 8000,
    [switch]$QuickTunnel
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Py = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$Runtime = Join-Path $Root "storage\runtime"
$Logs = Join-Path $Root "storage\logs"
New-Item -ItemType Directory -Force -Path $Runtime, $Logs | Out-Null

& $Py -c "from backend.config import validate_runtime_config; p=validate_runtime_config(); raise SystemExit('; '.join(p) if p else 0)"
$AppOut = Join-Path $Logs "beta-app.out.log"
$AppErr = Join-Path $Logs "beta-app.err.log"
$CmdExe = Join-Path $env:SystemRoot "System32\cmd.exe"
$AppCommand = "cd /d `"$Root`" && `"$Py`" -m uvicorn main_app:app --host 127.0.0.1 --port $Port --workers 1 1> `"$AppOut`" 2> `"$AppErr`""
$Process = Start-Process -FilePath $CmdExe -ArgumentList @("/c", $AppCommand) -WorkingDirectory $Root -WindowStyle Hidden -PassThru

$Ready = $false
for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
    try {
        $Response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/health/ready" -TimeoutSec 2
        if ($Response.StatusCode -eq 200) { $Ready = $true; break }
    } catch {}
    Start-Sleep -Milliseconds 500
}
if (-not $Ready) { throw "Beta app did not become ready. See $AppErr" }
$AppOwner = Get-Process python -ErrorAction Stop | Where-Object { $_.Path -eq $Py } | Sort-Object StartTime -Descending | Select-Object -First 1 -ExpandProperty Id
if (-not $AppOwner) { $AppOwner = $Process.Id }
Set-Content -LiteralPath (Join-Path $Runtime "beta-app.pid") -Value $AppOwner

$Result = [ordered]@{ app_pid = $AppOwner; local_url = "http://127.0.0.1:$Port"; worker_count = 1; app_log = $AppOut; error_log = $AppErr }
if ($QuickTunnel) {
    $Cloudflared = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
    if (-not $Cloudflared) { throw "cloudflared was not found on PATH" }
    $TunnelOut = Join-Path $Logs "beta-tunnel.out.log"
    $TunnelErr = Join-Path $Logs "beta-tunnel.err.log"
    Remove-Item -LiteralPath $TunnelOut, $TunnelErr -Force -ErrorAction SilentlyContinue
    $TunnelCommand = "cd /d `"$Root`" && `"$Cloudflared`" tunnel --url http://127.0.0.1:$Port --no-autoupdate 1> `"$TunnelOut`" 2> `"$TunnelErr`""
    $Tunnel = Start-Process -FilePath $CmdExe -ArgumentList @("/c", $TunnelCommand) -WorkingDirectory $Root -WindowStyle Hidden -PassThru
    $Result["tunnel_log"] = $TunnelErr
    $ExternalUrl = ""
    for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
        if (Test-Path -LiteralPath $TunnelErr) {
            $Matches = [regex]::Matches((Get-Content -Raw -LiteralPath $TunnelErr), 'https://[a-z0-9-]+\.trycloudflare\.com')
            $Candidate = $Matches | Where-Object { $_.Value -ne 'https://api.trycloudflare.com' } | Select-Object -Last 1
            if ($Candidate) { $ExternalUrl = $Candidate.Value; break }
        }
        Start-Sleep -Milliseconds 500
    }
    if (-not $ExternalUrl) { throw "Quick tunnel URL was not emitted. See $TunnelErr" }
    $TunnelOwner = Get-Process cloudflared -ErrorAction Stop | Sort-Object StartTime -Descending | Select-Object -First 1 -ExpandProperty Id
    Set-Content -LiteralPath (Join-Path $Runtime "beta-tunnel.pid") -Value $TunnelOwner
    $Result["tunnel_pid"] = $TunnelOwner
    $Result["external_url"] = $ExternalUrl
}
$Result | ConvertTo-Json -Compress
