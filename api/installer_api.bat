@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║         GéoClic V12 Pro - Installation de l'API                   ║
echo ║         Script d'installation automatisé                          ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

:: ═══════════════════════════════════════════════════════════════════════
:: ÉTAPE 1: Demander les informations de base de données
:: ═══════════════════════════════════════════════════════════════════════

echo [ÉTAPE 1/5] Configuration de la base de données
echo ------------------------------------------------
echo.

set /p DB_HOST="Hôte PostgreSQL (défaut: localhost): "
if "!DB_HOST!"=="" set DB_HOST=localhost

set /p DB_PORT="Port PostgreSQL (défaut: 5432): "
if "!DB_PORT!"=="" set DB_PORT=5432

set /p DB_NAME="Nom de la base de données (défaut: geoclic_v12): "
if "!DB_NAME!"=="" set DB_NAME=geoclic_v12

set /p DB_USER="Utilisateur PostgreSQL: "
if "!DB_USER!"=="" (
    echo ERREUR: L'utilisateur est obligatoire!
    pause
    exit /b 1
)

set /p DB_PASSWORD="Mot de passe PostgreSQL: "
if "!DB_PASSWORD!"=="" (
    echo ERREUR: Le mot de passe est obligatoire!
    pause
    exit /b 1
)

echo.
echo Configuration:
echo   - Hôte: !DB_HOST!
echo   - Port: !DB_PORT!
echo   - Base: !DB_NAME!
echo   - User: !DB_USER!
echo   - Pass: ********
echo.

:: ═══════════════════════════════════════════════════════════════════════
:: ÉTAPE 2: Vérifier Python
:: ═══════════════════════════════════════════════════════════════════════

echo [ÉTAPE 2/5] Vérification de Python
echo -----------------------------------

python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installé ou pas dans le PATH!
    echo Téléchargez-le sur: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python trouvé: %PYTHON_VERSION%
echo.

:: ═══════════════════════════════════════════════════════════════════════
:: ÉTAPE 3: Créer l'environnement virtuel
:: ═══════════════════════════════════════════════════════════════════════

echo [ÉTAPE 3/5] Création de l'environnement virtuel
echo -------------------------------------------------

if exist venv (
    echo Environnement virtuel existant trouvé.
    set /p RECREATE="Voulez-vous le recréer? (o/N): "
    if /i "!RECREATE!"=="o" (
        echo Suppression de l'ancien environnement...
        rmdir /s /q venv
        echo Création du nouvel environnement...
        python -m venv venv
    )
) else (
    echo Création de l'environnement virtuel...
    python -m venv venv
)

if not exist venv\Scripts\activate.bat (
    echo ERREUR: Échec de la création de l'environnement virtuel!
    pause
    exit /b 1
)

echo Environnement virtuel prêt.
echo.

:: ═══════════════════════════════════════════════════════════════════════
:: ÉTAPE 4: Installer les dépendances
:: ═══════════════════════════════════════════════════════════════════════

echo [ÉTAPE 4/5] Installation des dépendances
echo -----------------------------------------

call venv\Scripts\activate.bat

echo Mise à jour de pip...
python -m pip install --upgrade pip >nul 2>&1

echo Installation des dépendances (cela peut prendre quelques minutes)...
pip install -r requirements.txt

if errorlevel 1 (
    echo ERREUR: Échec de l'installation des dépendances!
    pause
    exit /b 1
)

echo Dépendances installées avec succès.
echo.

:: ═══════════════════════════════════════════════════════════════════════
:: ÉTAPE 5: Créer le fichier .env avec les credentials
:: ═══════════════════════════════════════════════════════════════════════

echo [ÉTAPE 5/5] Configuration de l'application
echo -------------------------------------------

:: Créer le fichier .env
echo # GéoClic V12 Pro - Configuration> .env
echo # Généré automatiquement le %date% à %time%>> .env
echo.>> .env
echo # Base de données>> .env
echo DATABASE_URL=postgresql+asyncpg://!DB_USER!:!DB_PASSWORD!@!DB_HOST!:!DB_PORT!/!DB_NAME!>> .env
echo.>> .env
echo # Sécurité (changez en production!)>> .env
echo SECRET_KEY=dev_secret_key_change_in_production>> .env
echo.>> .env
echo # CORS>> .env
echo ALLOWED_ORIGINS_STR=http://localhost:3000,http://localhost:8080,http://localhost:5000,http://localhost:8000>> .env

echo Fichier .env créé avec les credentials.
echo.

:: ═══════════════════════════════════════════════════════════════════════
:: TERMINÉ
:: ═══════════════════════════════════════════════════════════════════════

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║                    INSTALLATION TERMINÉE !                        ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.
echo Pour lancer l'API:
echo.
echo   1. Ouvrez un terminal dans ce dossier
echo   2. Tapez: venv\Scripts\activate.bat
echo   3. Tapez: uvicorn main:app --reload --host 0.0.0.0 --port 8000
echo.
echo Ou utilisez le script: lancer_api.bat
echo.
echo Documentation API: http://localhost:8000/docs
echo.

:: Créer aussi un script de lancement rapide
echo @echo off> lancer_api.bat
echo cd /d "%%~dp0">> lancer_api.bat
echo call venv\Scripts\activate.bat>> lancer_api.bat
echo echo.>> lancer_api.bat
echo echo Lancement de GéoClic V12 Pro API...>> lancer_api.bat
echo echo Documentation: http://localhost:8000/docs>> lancer_api.bat
echo echo.>> lancer_api.bat
echo uvicorn main:app --reload --host 0.0.0.0 --port 8000>> lancer_api.bat

echo Script de lancement rapide créé: lancer_api.bat
echo.

set /p LAUNCH_NOW="Voulez-vous lancer l'API maintenant? (O/n): "
if /i "!LAUNCH_NOW!"=="n" (
    echo.
    echo À bientôt!
    pause
    exit /b 0
)

echo.
echo Lancement de l'API...
uvicorn main:app --reload --host 0.0.0.0 --port 8000
