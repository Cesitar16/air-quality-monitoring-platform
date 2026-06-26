$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

& python src/clustering.py @args
exit $LASTEXITCODE
