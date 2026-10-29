# Starts the Flask API and the Vite dev server in two new PowerShell windows.
$root = $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path (Join-Path $root "backend\.env"))) {
    Write-Warning "backend\.env not found - copy backend\.env.example to backend\.env and set DB_PASSWORD first."
    exit 1
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\backend'; & '$python' run.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\frontend'; npm run dev"
Write-Host "API   -> http://localhost:5000/api/v1/health"
Write-Host "UI    -> http://localhost:5173"
