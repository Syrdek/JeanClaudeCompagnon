$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

function Write-Step {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Get-CudaVersion {
    # Retourne une version du type "12.6" ou $null
    $cudaVersion = $null

    # 1) Essayer nvcc
    $nvcc = Get-Command nvcc -ErrorAction SilentlyContinue
    if ($nvcc) {
        try {
            $nvccOutput = & nvcc --version 2>&1 | Out-String
            if ($nvccOutput -match 'release\s+(\d+\.\d+)') {
                return $Matches[1]
            }
        } catch {}
    }

    # 2) Essayer nvidia-smi
    $nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($nvidiaSmi) {
        try {
            $smiOutput = & nvidia-smi 2>&1 | Out-String
            if ($smiOutput -match 'CUDA Version:\s+(\d+\.\d+)') {
                return $Matches[1]
            }
        } catch {}
    }

    return $null
}

function Get-PyTorchIndexUrl {
    param([string]$CudaVersion)

    if (-not $CudaVersion) {
        return $null
    }

    # Mapping basé sur les index CUDA publiés par PyTorch
    $majorMinor = $CudaVersion

    switch -Regex ($majorMinor) {
        '^13\.0' { return 'https://download.pytorch.org/whl/cu130' }
        '^12\.8' { return 'https://download.pytorch.org/whl/cu128' }
        '^12\.7' { return 'https://download.pytorch.org/whl/cu126' } # fallback vers la plus proche supportée
        '^12\.6' { return 'https://download.pytorch.org/whl/cu126' }
        '^12\.5' { return 'https://download.pytorch.org/whl/cu124' } # fallback
        '^12\.4' { return 'https://download.pytorch.org/whl/cu124' }
        '^12\.3' { return 'https://download.pytorch.org/whl/cu124' } # fallback
        '^12\.2' { return 'https://download.pytorch.org/whl/cu121' } # fallback ancien support
        '^12\.1' { return 'https://download.pytorch.org/whl/cu121' }
        '^12\.0' { return 'https://download.pytorch.org/whl/cu121' } # fallback
        '^11\.8' { return 'https://download.pytorch.org/whl/cu118' }
        '^11\.[0-7]' { return 'https://download.pytorch.org/whl/cu118' } # fallback moderne le plus proche encore courant
        default { return $null }
    }
}

function Test-Python312Installed {
    try {
        $output = & py -3.12 --version 2>&1 | Out-String
        return ($LASTEXITCODE -eq 0 -and $output -match '^Python 3\.12(\.\d+)?')
    } catch {
        return $false
    }
}

function Install-Python312 {
    Write-Step "Vérification de Python 3.12"

    if (Test-Python312Installed) {
        Write-Host "Python 3.12 est déjà installé."
        return
    }

    Write-Host "Python 3.12 non détecté. Installation en cours..."

    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "winget est introuvable. Impossible d'installer automatiquement Python 3.12."
    }

    & winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements

    if (-not (Test-Python312Installed)) {
        throw "Python 3.12 n'a pas été détecté après l'installation."
    }

    Write-Host "Python 3.12 installé avec succès."
}

Install-Python312

Write-Step "Vérification / création du virtualenv"
if (-not (Test-Path ".venv")) {
    Write-Host "Création de .venv..."
    py -3.12 -m venv .venv
} else {
    Write-Host ".venv existe déjà."
}

Write-Step "Activation du virtualenv"
$activateScript = Join-Path $PWD ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    throw "Script d'activation introuvable: $activateScript"
}
. $activateScript

Write-Step "Mise à jour de pip"
python -m pip install --upgrade pip

Write-Step "Détection de CUDA"
$cudaVersion = Get-CudaVersion
if ($cudaVersion) {
    Write-Host "CUDA détecté: $cudaVersion"
} else {
    Write-Host "CUDA non détecté. Installation de la version par défaut de torch/torchvision."
}

Write-Step "Installation de torch / torchvision"
$torchIndexUrl = Get-PyTorchIndexUrl -CudaVersion $cudaVersion

if ($torchIndexUrl) {
    Write-Host "Utilisation de l'index PyTorch: $torchIndexUrl"
    python -m pip install torch torchvision --index-url $torchIndexUrl
} else {
    Write-Host "Aucun index CUDA compatible trouvé, installation par défaut."
    python -m pip install torch torchvision
}

Write-Step "Installation des dépendances requirements.txt"
if (Test-Path "requirements.txt") {
    python -m pip install -r requirements.txt
} else {
    Write-Host "requirements.txt introuvable, étape ignorée." -ForegroundColor Yellow
}

Write-Step "Création du dossier models"
if (-not (Test-Path "models")) {
    New-Item -ItemType Directory -Path "models" | Out-Null
    Write-Host "Dossier models créé."
} else {
    Write-Host "Le dossier models existe déjà."
}

Write-Step "Création du lancement automatique au démarrage de session"
$startupFolder = [Environment]::GetFolderPath("Startup")
$runScriptPath = Join-Path $PSScriptRoot "run.ps1"
$batPath = Join-Path $startupFolder "JeanClaudeCompagnon.bat"

if (-not (Test-Path $runScriptPath)) {
    throw "Script run.ps1 introuvable: $runScriptPath"
}

if (Test-Path $batPath) {
    Write-Host "Le fichier existe déjà, aucune modification: $batPath" -ForegroundColor Yellow
} else {
    $batContent = @"
@echo off
powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "$runScriptPath"
"@

    Set-Content -Path $batPath -Value $batContent -Encoding ASCII
    Write-Host "Fichier de démarrage créé: $batPath"
}

Write-Step "Terminé"
Write-Host "Environnement prêt."