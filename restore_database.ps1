param(
    [Parameter(Mandatory = $true)]
    [string]$BackupPath,
    [string]$DatabasePath = ".\auction_data.db",
    [switch]$DryRun,
    [switch]$ConfirmRestore
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path -LiteralPath $BackupPath)) {
    throw "Backup file not found: $BackupPath"
}

$resolvedBackup = Resolve-Path -LiteralPath $BackupPath
$targetParent = Split-Path -Parent $DatabasePath
if ($targetParent -and -not (Test-Path -LiteralPath $targetParent)) {
    throw "Database directory does not exist: $targetParent"
}

$hash = Get-FileHash -Algorithm SHA256 -LiteralPath $resolvedBackup.Path
$info = @{
    backup = $resolvedBackup.Path
    target = (Join-Path $ProjectRoot $DatabasePath)
    sha256 = $hash.Hash
    dry_run = [bool]$DryRun
    confirm_restore = [bool]$ConfirmRestore
}

if ($DryRun -or -not $ConfirmRestore) {
    $info["status"] = "DRY_RUN_ONLY"
    $info | ConvertTo-Json -Compress
    exit 0
}

Copy-Item -LiteralPath $resolvedBackup.Path -Destination $DatabasePath -Force
$info["status"] = "RESTORED"
$info | ConvertTo-Json -Compress
