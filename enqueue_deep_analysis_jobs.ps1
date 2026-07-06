param(
    [int]$Limit = 20
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location $ProjectRoot

& $PythonExe -c "from backend.database.session import init_db, session_scope; from backend.jobs.scheduler import enqueue_missing_deep_analysis_jobs; init_db(); s=session_scope(); session=s.__enter__(); result=enqueue_missing_deep_analysis_jobs(session, limit=$Limit); s.__exit__(None,None,None); import json; print(json.dumps(result, ensure_ascii=False))"
