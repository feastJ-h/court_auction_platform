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

$Py = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$RehearsalDir = Join-Path $ProjectRoot "storage\restore-rehearsal"
New-Item -ItemType Directory -Force -Path $RehearsalDir | Out-Null
$TempDb = Join-Path $RehearsalDir ("restore_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".db")
Copy-Item -LiteralPath $BackupPath -Destination $TempDb

$env:DB_URL = "sqlite:///$($TempDb.Replace('\','/'))"
& $Py -c "from backend.database.session import init_db; init_db(); print('new_code_startup=PASS')"
if ($LASTEXITCODE -ne 0) { throw "New code startup against restored DB failed." }
$AuditJson = & $Py -c "import json,sqlite3,sys; c=sqlite3.connect(sys.argv[1]); integrity=c.execute('PRAGMA integrity_check').fetchone()[0]; names=['users','auction_items','auction_notices','audit_logs']; counts={n:c.execute('SELECT COUNT(*) FROM '+n).fetchone()[0] for n in names}; print(json.dumps({'integrity':integrity,'counts':counts}))" $TempDb
if ($LASTEXITCODE -ne 0) { throw "Restore integrity/count audit failed." }
$Hash = Get-FileHash -Algorithm SHA256 -LiteralPath $TempDb
[ordered]@{ status = "PASS"; source = (Resolve-Path -LiteralPath $BackupPath).Path; restored = $TempDb; sha256 = $Hash.Hash; audit = ($AuditJson | ConvertFrom-Json) } | ConvertTo-Json -Depth 4 -Compress
