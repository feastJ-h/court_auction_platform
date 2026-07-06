param(
    [string]$DatabasePath = ".\auction_data.db",
    [string]$BackupDir = ".\storage\backups"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path $DatabasePath)) {
    throw "Database file not found: $DatabasePath"
}

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$source = Resolve-Path $DatabasePath
$target = Join-Path $BackupDir "auction_data_$timestamp.db"
Copy-Item -LiteralPath $source -Destination $target -Force

$hash = Get-FileHash -Algorithm SHA256 -LiteralPath $target
Write-Output (@{
    source = $source.Path
    backup = (Resolve-Path $target).Path
    sha256 = $hash.Hash
} | ConvertTo-Json -Compress)
