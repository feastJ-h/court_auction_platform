param(
    [switch]$Visual
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Py = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (-not (Test-Path -LiteralPath $Py)) {
    throw "Bundled Python runtime was not found."
}

Push-Location $ProjectRoot
try {
    Write-Host "[1/8] Python compile"
    & $Py -m py_compile main_app.py backend\web\pagination.py backend\web\routers\auctions.py backend\web\routers\cases.py backend\services\auction_items.py backend\services\onbid_review.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "[2/8] Default product pytest"
    & $Py -m pytest -m "not integration and not external and not visual"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "[3/8] Legacy isolated scripts"
    foreach ($TestScript in @("tests/onbid_module_test.py", "tests/page_response_smoke_test.py", "tests/router_boundary_test.py", "tests/isolated_operations_test.py")) {
        & $Py $TestScript
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }

    Write-Host "[4/8] Public banned-copy scan"
    $PublicFiles = @(
        "frontend/templates/public/home.html",
        "frontend/templates/public/about.html",
        "frontend/templates/public/terms.html",
        "frontend/templates/public/privacy_draft.html",
        "frontend/templates/public/disclaimer.html",
        "frontend/templates/auctions/index.html",
        "frontend/templates/auctions/today.html",
        "frontend/templates/cases/index.html"
    )
    $Banned = "AI 분석|권리분석|낙찰 보장|명도 쉬움|전문가 보고서|공식 파트너|돈 되는 물건|완벽한 분석"
    $BannedHits = Select-String -Path $PublicFiles -Pattern $Banned
    if ($BannedHits) {
        $BannedHits | ForEach-Object { Write-Error ("Banned public copy: {0}:{1}" -f $_.Path, $_.LineNumber) }
        exit 1
    }

    Write-Host "[5/8] Mojibake scan"
    $TextFiles = Get-ChildItem -Recurse -File backend,frontend | Where-Object { $_.Extension -in @(".py", ".html", ".js") }
    $MojibakeHits = $TextFiles | Select-String -Pattern "�|\?쒕|\?먮|\?곗"
    if ($MojibakeHits) {
        $MojibakeHits | ForEach-Object { Write-Error ("Mojibake: {0}:{1}" -f $_.Path, $_.LineNumber) }
        exit 1
    }

    Write-Host "[6/8] Route smoke"
    & $Py tests\page_response_smoke_test.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "[7/8] Optional visual QA"
    if ($Visual) {
        & $Py -m pytest -m visual
        if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 5) { exit $LASTEXITCODE }
    } else {
        Write-Host "Visual suite skipped (use -Visual when a browser target is available)."
    }

    Write-Host "[8/8] Sensitive staged-file scan"
    $Sensitive = git diff --cached --name-only | Select-String -Pattern '(^|/|\\)(\.env|storage|logs)(/|\\|$)|\.(db|sqlite|sqlite3)$|runtime_settings\.json|\.git\.bad-init'
    if ($Sensitive) {
        $Sensitive | ForEach-Object { Write-Error ("Sensitive staged file: {0}" -f $_.Line) }
        exit 1
    }

    Write-Host "PASS - beta QA"
} finally {
    Pop-Location
}
