$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

Write-Step "Activation du virtualenv"
$activateScript = Join-Path $PWD ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    throw "Script d'activation introuvable: $activateScript"
}
. $activateScript

python main.py