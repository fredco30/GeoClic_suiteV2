# ═══════════════════════════════════════════════════════════════════════════════
# Lanceur GéoClic SIG Desktop - Windows PowerShell
# Gère l'installation, la configuration initiale et les mises à jour
# ═══════════════════════════════════════════════════════════════════════════════

param(
    [switch]$Install,
    [switch]$Update,
    [switch]$CheckUpdate,
    [switch]$Uninstall,
    [switch]$Version,
    [switch]$Help
)

# Configuration
$AppName = "GeoClicSIG"
$AppDisplayName = "GéoClic SIG"
$AppVersion = "14.0.0"
$InstallDir = "$env:LOCALAPPDATA\$AppName"
$ConfigDir = "$env:APPDATA\$AppName"
$DownloadUrl = "https://releases.geoclic.fr/sig/windows/latest"

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Success { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Warn { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

function Show-Banner {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "   $AppDisplayName v$AppVersion" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# VÉRIFICATION DE L'INSTALLATION
# ═══════════════════════════════════════════════════════════════════════════════
function Test-Installation {
    return Test-Path "$InstallDir\geoclic_sig.exe"
}

# ═══════════════════════════════════════════════════════════════════════════════
# INSTALLATION
# ═══════════════════════════════════════════════════════════════════════════════
function Install-App {
    Write-Info "Installation de $AppDisplayName..."

    # Créer les répertoires
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null

    # Vérifier si le bundle est dans le même dossier
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $LocalExe = Join-Path $ScriptDir "geoclic_sig.exe"

    if (Test-Path $LocalExe) {
        Write-Info "Installation depuis le dossier local..."
        Copy-Item "$ScriptDir\*" -Destination $InstallDir -Recurse -Force
    } else {
        # Télécharger depuis le serveur
        Write-Info "Téléchargement depuis $DownloadUrl..."

        $TmpFile = "$env:TEMP\geoclic-sig-latest.zip"

        try {
            Invoke-WebRequest -Uri $DownloadUrl -OutFile $TmpFile -UseBasicParsing
        } catch {
            Write-Error "Échec du téléchargement: $_"
            return
        }

        Write-Info "Extraction..."
        Expand-Archive -Path $TmpFile -DestinationPath $InstallDir -Force
        Remove-Item $TmpFile
    }

    # Créer le raccourci sur le bureau
    Create-Shortcut

    # Créer la configuration initiale
    Initialize-Config

    Write-Success "Installation terminée !"
}

# ═══════════════════════════════════════════════════════════════════════════════
# CRÉATION DU RACCOURCI
# ═══════════════════════════════════════════════════════════════════════════════
function Create-Shortcut {
    $WshShell = New-Object -ComObject WScript.Shell

    # Raccourci Bureau
    $DesktopShortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\$AppDisplayName.lnk")
    $DesktopShortcut.TargetPath = "$InstallDir\geoclic_sig.exe"
    $DesktopShortcut.WorkingDirectory = $InstallDir
    $DesktopShortcut.Description = "Application SIG pour la gestion territoriale"
    $DesktopShortcut.Save()

    # Raccourci Menu Démarrer
    $StartMenuDir = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\$AppDisplayName"
    New-Item -ItemType Directory -Force -Path $StartMenuDir | Out-Null

    $StartMenuShortcut = $WshShell.CreateShortcut("$StartMenuDir\$AppDisplayName.lnk")
    $StartMenuShortcut.TargetPath = "$InstallDir\geoclic_sig.exe"
    $StartMenuShortcut.WorkingDirectory = $InstallDir
    $StartMenuShortcut.Description = "Application SIG pour la gestion territoriale"
    $StartMenuShortcut.Save()

    Write-Success "Raccourcis créés"
}

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION INITIALE
# ═══════════════════════════════════════════════════════════════════════════════
function Initialize-Config {
    $ConfigFile = "$ConfigDir\config.json"

    if (-not (Test-Path $ConfigFile)) {
        Write-Info "Création de la configuration initiale..."

        $Config = @{
            api_url = ""
            connection_mode = "api"
            agent_name = ""
            offline_mode = $false
            auto_sync = $true
            sync_interval_minutes = 5
            map_cache_enabled = $true
            photo_quality = "high"
        }

        $Config | ConvertTo-Json | Out-File -FilePath $ConfigFile -Encoding UTF8

        Write-Info "Configuration créée dans $ConfigFile"
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# VÉRIFICATION DES MISES À JOUR
# ═══════════════════════════════════════════════════════════════════════════════
function Test-Update {
    Write-Info "Vérification des mises à jour..."

    try {
        $CurrentVersion = Get-Content "$InstallDir\version.txt" -ErrorAction SilentlyContinue
        if (-not $CurrentVersion) { $CurrentVersion = "0.0.0" }

        $LatestVersion = (Invoke-WebRequest -Uri "https://releases.geoclic.fr/sig/version.txt" -UseBasicParsing).Content.Trim()

        if ($LatestVersion -ne $CurrentVersion) {
            Write-Warn "Mise à jour disponible: $CurrentVersion -> $LatestVersion"

            $Response = Read-Host "Voulez-vous mettre à jour maintenant ? (O/N)"
            if ($Response -eq "O" -or $Response -eq "o") {
                Update-App
            }
        } else {
            Write-Success "Vous avez la dernière version ($CurrentVersion)"
        }
    } catch {
        Write-Warn "Impossible de vérifier les mises à jour"
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# MISE À JOUR
# ═══════════════════════════════════════════════════════════════════════════════
function Update-App {
    Write-Info "Mise à jour de $AppDisplayName..."

    # Sauvegarder la configuration
    $BackupDir = "$env:TEMP\geoclic-sig-backup"
    if (Test-Path "$InstallDir\data") {
        Copy-Item "$InstallDir\data" -Destination $BackupDir -Recurse -Force
    }

    # Télécharger
    $TmpFile = "$env:TEMP\geoclic-sig-latest.zip"
    try {
        Invoke-WebRequest -Uri $DownloadUrl -OutFile $TmpFile -UseBasicParsing
    } catch {
        Write-Error "Échec du téléchargement"
        return
    }

    # Supprimer l'ancienne version
    Remove-Item "$InstallDir\*" -Recurse -Force

    # Extraire
    Expand-Archive -Path $TmpFile -DestinationPath $InstallDir -Force
    Remove-Item $TmpFile

    # Restaurer la configuration
    if (Test-Path $BackupDir) {
        Copy-Item "$BackupDir\*" -Destination "$InstallDir\data" -Recurse -Force
        Remove-Item $BackupDir -Recurse -Force
    }

    Write-Success "Mise à jour terminée !"
}

# ═══════════════════════════════════════════════════════════════════════════════
# DÉSINSTALLATION
# ═══════════════════════════════════════════════════════════════════════════════
function Uninstall-App {
    Write-Info "Désinstallation de $AppDisplayName..."

    # Supprimer l'installation
    if (Test-Path $InstallDir) {
        Remove-Item $InstallDir -Recurse -Force
    }

    # Supprimer la configuration (demander)
    if (Test-Path $ConfigDir) {
        $Response = Read-Host "Supprimer aussi la configuration ? (O/N)"
        if ($Response -eq "O" -or $Response -eq "o") {
            Remove-Item $ConfigDir -Recurse -Force
        }
    }

    # Supprimer les raccourcis
    Remove-Item "$env:USERPROFILE\Desktop\$AppDisplayName.lnk" -ErrorAction SilentlyContinue
    Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\$AppDisplayName" -Recurse -ErrorAction SilentlyContinue

    Write-Success "Désinstallation terminée"
}

# ═══════════════════════════════════════════════════════════════════════════════
# LANCEMENT DE L'APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════
function Start-App {
    $ExePath = "$InstallDir\geoclic_sig.exe"

    if (-not (Test-Path $ExePath)) {
        Write-Error "Application non trouvée. Lancez avec -Install pour installer."
        return
    }

    # Définir les variables d'environnement
    $env:GEOCLIC_CONFIG_DIR = $ConfigDir
    $env:GEOCLIC_VERSION = $AppVersion

    # Lancer l'application
    Start-Process -FilePath $ExePath -WorkingDirectory $InstallDir
}

# ═══════════════════════════════════════════════════════════════════════════════
# SCRIPT PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
Show-Banner

if ($Help) {
    Write-Host "Usage: .\geoclic-sig-windows.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Install       Installer l'application"
    Write-Host "  -Update        Forcer la mise à jour"
    Write-Host "  -CheckUpdate   Vérifier les mises à jour"
    Write-Host "  -Uninstall     Désinstaller l'application"
    Write-Host "  -Version       Afficher la version"
    Write-Host "  -Help          Afficher cette aide"
    Write-Host ""
    Write-Host "Sans option: lance l'application (installe si nécessaire)"
    exit
}

if ($Version) {
    Write-Host "$AppDisplayName v$AppVersion"
    exit
}

if ($Uninstall) {
    Uninstall-App
    exit
}

if ($Install) {
    Install-App
    exit
}

if ($Update) {
    if (-not (Test-Installation)) {
        Write-Error "Application non installée"
        exit
    }
    Update-App
    exit
}

if ($CheckUpdate) {
    if (-not (Test-Installation)) {
        Write-Error "Application non installée"
        exit
    }
    Test-Update
    exit
}

# Comportement par défaut: installer si nécessaire et lancer
if (-not (Test-Installation)) {
    Install-App
}

# Vérifier les mises à jour en arrière-plan
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 5
    # Vérification silencieuse
} | Out-Null

Start-App
