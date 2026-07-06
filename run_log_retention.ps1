param(
    [switch]$DryRun = $true,
    [switch]$Apply,
    [switch]$LogsOnly,
    [int]$OnbidLogDays = 30,
    [int]$AppLogDays = 30,
    [int]$BackupDays = 30
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$targets = @(
    @{ Path = "storage\logs\onbid"; Pattern = "*.log"; Days = $OnbidLogDays; Label = "onbid_logs" },
    @{ Path = "."; Pattern = "*.log"; Days = $AppLogDays; Label = "app_logs" }
)

if (-not $LogsOnly) {
    $targets += @{ Path = "storage\backups"; Pattern = "*.db"; Days = $BackupDays; Label = "db_backups" }
}

$now = Get-Date
$candidates = @()
foreach ($target in $targets) {
    if (-not (Test-Path -LiteralPath $target.Path)) {
        continue
    }
    $cutoff = $now.AddDays(-1 * [int]$target.Days)
    Get-ChildItem -LiteralPath $target.Path -Filter $target.Pattern -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $cutoff } |
        ForEach-Object {
            $candidates += [pscustomobject]@{
                label = $target.Label
                path = $_.FullName
                last_write_time = $_.LastWriteTime
                bytes = $_.Length
            }
        }
}

$candidates | ConvertTo-Json -Compress

if ($Apply) {
    foreach ($candidate in $candidates) {
        Remove-Item -LiteralPath $candidate.path -Force
    }
    Write-Output "Applied log retention to listed log/backup files only."
} else {
    Write-Output "Dry-run only. Re-run with -Apply to delete listed log/backup files."
}
