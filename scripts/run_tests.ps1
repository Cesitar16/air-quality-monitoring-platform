$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

$ReportDir = Join-Path $RepoRoot "tests\reports"
$ReportPath = Join-Path $ReportDir "pytest_result.txt"

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

& python -m pytest -q 2>&1 | Tee-Object -FilePath $ReportPath
$exitCode = $LASTEXITCODE

exit $exitCode
