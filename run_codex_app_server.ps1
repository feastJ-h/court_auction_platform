param(
    [string]$Endpoint = "ws://127.0.0.1:4500"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

codex app-server --listen $Endpoint
