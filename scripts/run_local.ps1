Param(
    [switch]$SkipInstall,
    [switch]$SkipInit,
    [switch]$NoServer
)

Set-StrictMode -Version Latest

$projectRoot = (Resolve-Path "$PSScriptRoot\..").Path
$venvPath = Join-Path $projectRoot ".venv"

function Write-Info($msg) { Write-Host "[ultima] $msg" -ForegroundColor Cyan }
function Write-Err($msg)  { Write-Host "[ultima] $msg" -ForegroundColor Red }

# Ensure we run from project root so module imports work
Push-Location $projectRoot
$env:PYTHONPATH = $projectRoot

# Create venv if missing
if (-not (Test-Path (Join-Path $venvPath "Scripts\python.exe"))) {
    Write-Info "Creating virtual environment..."
    & python -m venv $venvPath
}

$python = Join-Path $venvPath "Scripts\python.exe"

# Install dependencies
if (-not $SkipInstall) {
    Write-Info "Installing requirements..."
    & $python -m pip install --quiet --upgrade pip
    & $python -m pip install --quiet -r (Join-Path $projectRoot "requirements.txt")
}

# Initialize Qdrant collection
if (-not $SkipInit) {
    Write-Info "Initializing Qdrant collection..."
    & $python -m scripts.init_qdrant
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Qdrant init failed. Is the Qdrant container running? (docker ps)"
        Pop-Location
        return
    }
}

# Launch Streamlit
if (-not $NoServer) {
    Write-Info "Starting Streamlit at http://localhost:8501 ..."
    & $python -m streamlit run src/app.py
} else {
    Write-Info "Setup complete. Skipped starting Streamlit (NoServer set)."
}

Pop-Location
