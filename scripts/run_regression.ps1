$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

& python src/regression.py @args
exit $LASTEXITCODE
