$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

if ($args.Count -eq 0) {
    & python etl/run_pipeline.py --dry-run
    exit $LASTEXITCODE
}

& python etl/run_pipeline.py @args
exit $LASTEXITCODE
