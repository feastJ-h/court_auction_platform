param(
    [string]$BackupPath = ""
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not $BackupPath) {
    $latest = Get-ChildItem -LiteralPath "storage\backups" -Filter "*.db" -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($null -eq $latest) {
        throw "No backup DB found under storage\backups for restore rehearsal."
    }
    $BackupPath = $latest.FullName
}

powershell -ExecutionPolicy Bypass -File .\restore_database.ps1 -BackupPath $BackupPath -DryRun
