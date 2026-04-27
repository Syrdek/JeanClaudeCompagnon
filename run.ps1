$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

function Write-Step {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

Write-Step "Activation du virtualenv"
$activateScript = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    throw "Script d'activation introuvable: $activateScript"
}
. $activateScript

Write-Step "Lancement de l'application Python"

python main.py