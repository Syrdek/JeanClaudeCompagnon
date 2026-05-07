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

    # Mapping base sur les index CUDA publies par PyTorch
    $majorMinor = $CudaVersion

    switch -Regex ($majorMinor) {
        '^13\.0' { return 'https://download.pytorch.org/whl/cu130' }
        '^12\.8' { return 'https://download.pytorch.org/whl/cu128' }
        '^12\.7' { return 'https://download.pytorch.org/whl/cu126' }
        '^12\.6' { return 'https://download.pytorch.org/whl/cu126' }
        '^12\.5' { return 'https://download.pytorch.org/whl/cu124' }
        '^12\.4' { return 'https://download.pytorch.org/whl/cu124' }
        '^12\.3' { return 'https://download.pytorch.org/whl/cu124' }
        '^12\.2' { return 'https://download.pytorch.org/whl/cu121' }
        '^12\.1' { return 'https://download.pytorch.org/whl/cu121' }
        '^12\.0' { return 'https://download.pytorch.org/whl/cu121' }
        '^11\.8' { return 'https://download.pytorch.org/whl/cu118' }
        '^11\.[0-7]' { return 'https://download.pytorch.org/whl/cu118' }
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
    Write-Step "Verification de Python 3.12"

    if (Test-Python312Installed) {
        Write-Host "Python 3.12 est deja installe."
        return
    }

    Write-Host "Python 3.12 non detecte. Installation en cours..."

    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "winget est introuvable. Impossible d'installer automatiquement Python 3.12."
    }

    & winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements

    if (-not (Test-Python312Installed)) {
        throw "Python 3.12 n'a pas ete detecte apres l'installation."
    }

    Write-Host "Python 3.12 installe avec succes."
}

function New-StartupShortcut {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ShortcutPath,

        [Parameter(Mandatory = $true)]
        [string]$RunScriptPath,

        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory
    )

    $powershellExe = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $arguments = '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "{0}"' -f $RunScriptPath

    $wshShell = New-Object -ComObject WScript.Shell
    $shortcut = $wshShell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $powershellExe
    $shortcut.Arguments = $arguments
    $shortcut.WorkingDirectory = $WorkingDirectory
    $shortcut.IconLocation = "$powershellExe,0"
    $shortcut.Save()
}

function Ask-YesNo {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Question
    )

    while ($true) {
        $response = Read-Host "$Question [O/N]"
        if ($null -eq $response) {
            continue
        }

        switch ($response.Trim().ToLowerInvariant()) {
            'o' { return $true }
            'oui' { return $true }
            'y' { return $true }
            'yes' { return $true }
            'n' { return $false }
            'non' { return $false }
            'no' { return $false }
            default { Write-Host "Reponse invalide. Merci de repondre par O ou N." -ForegroundColor Yellow }
        }
    }
}

Install-Python312

Write-Step "Verification / creation du virtualenv"
if (-not (Test-Path ".venv")) {
    Write-Host "Creation de .venv..."
    py -3.12 -m venv .venv
} else {
    Write-Host ".venv existe deja."
}

Write-Step "Activation du virtualenv"
$activateScript = Join-Path $PWD ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    throw "Script d'activation introuvable: $activateScript"
}
. $activateScript

Write-Step "Mise a jour de pip"
python -m pip install --upgrade pip

Write-Step "Detection de CUDA"
$cudaVersion = Get-CudaVersion
if ($cudaVersion) {
    Write-Host "CUDA detecte: $cudaVersion"
} else {
    Write-Host "CUDA non detecte. Installation de la version par defaut de torch/torchvision."
}

Write-Step "Installation de torch / torchvision"
$torchIndexUrl = Get-PyTorchIndexUrl -CudaVersion $cudaVersion

if ($torchIndexUrl) {
    Write-Host "Utilisation de l'index PyTorch: $torchIndexUrl"
    python -m pip install torch torchvision --index-url $torchIndexUrl
} else {
    Write-Host "Aucun index CUDA compatible trouve, installation par defaut."
    python -m pip install torch torchvision
}

Write-Step "Installation des dependances requirements.txt"
if (Test-Path "requirements.txt") {
    python -m pip install -r requirements.txt
} else {
    Write-Host "requirements.txt introuvable, etape ignoree." -ForegroundColor Yellow
}

Write-Step "Creation du dossier models"
if (-not (Test-Path "models")) {
    New-Item -ItemType Directory -Path "models" | Out-Null
    Write-Host "Dossier models cree."
} else {
    Write-Host "Le dossier models existe deja."
}

Write-Step "Configuration du lancement automatique au demarrage de session"
$startupFolder = [Environment]::GetFolderPath("Startup")
$runScriptPath = Join-Path $PSScriptRoot "run.ps1"
$shortcutPath = Join-Path $startupFolder "JeanClaudeCompagnon.lnk"
$legacyBatPath = Join-Path $startupFolder "JeanClaudeCompagnon.bat"

if (-not (Test-Path $runScriptPath)) {
    throw "Script run.ps1 introuvable: $runScriptPath"
}

$enableStartup = Ask-YesNo "Souhaitez-vous lancer l'application automatiquement au démarrage de votre session Windows ?"

if ($enableStartup) {
    if (Test-Path $legacyBatPath) {
        Remove-Item $legacyBatPath -Force
        Write-Host "Ancien fichier .bat supprime: $legacyBatPath"
    }

    New-StartupShortcut -ShortcutPath $shortcutPath -RunScriptPath $runScriptPath -WorkingDirectory $PSScriptRoot
    Write-Host "Raccourci de démarrage créé ou mis à jour: $shortcutPath"
} else {
    if (Test-Path $shortcutPath) {
        Remove-Item $shortcutPath -Force
        Write-Host "Raccourci de demarrage supprime: $shortcutPath"
    } else {
        Write-Host "Aucun raccourci de demarrage cree."
    }

    if (Test-Path $legacyBatPath) {
        Remove-Item $legacyBatPath -Force
        Write-Host "Ancien fichier .bat supprime: $legacyBatPath"
    }
}

Write-Step "Termine"
Write-Host "Environnement pret."