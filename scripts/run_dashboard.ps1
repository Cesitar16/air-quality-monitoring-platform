$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

& streamlit run dashboards/app.py @args
exit $LASTEXITCODE
