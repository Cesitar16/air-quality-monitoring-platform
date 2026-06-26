$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

$PythonExe = Join-Path $RepoRoot ".venv\\Scripts\\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "No se encontro .venv\\Scripts\\python.exe." -ForegroundColor Yellow
    Write-Host "Crea o activa el entorno virtual antes de ejecutar el dashboard." -ForegroundColor Yellow
    Write-Host "Ejemplo:" -ForegroundColor DarkGray
    Write-Host "  python -m venv .venv" -ForegroundColor DarkGray
    Write-Host "  .\\.venv\\Scripts\\Activate.ps1" -ForegroundColor DarkGray
    Write-Host "  python -m pip install -r requirements.txt" -ForegroundColor DarkGray
    exit 1
}

& $PythonExe -m streamlit run dashboards/app.py @args
exit $LASTEXITCODE
