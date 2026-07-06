$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location -LiteralPath $ProjectRoot
& $PythonExe ".\tests\isolated_operations_test.py"
