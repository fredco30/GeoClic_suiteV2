@echo off
chcp 65001 >nul
echo.
echo ===============================================
echo    GéoClic V12 Pro - Lancement API FastAPI
echo ===============================================
echo.

REM Se placer dans le dossier api
cd /d "%~dp0api"

REM Vérifier que Python est installé
echo [1/3] Verification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou pas dans le PATH
    echo Telechargez Python sur https://www.python.org/downloads/
    pause
    exit /b 1
)
echo       Python OK

REM Installer les dépendances
echo [2/3] Installation des dependances (pip install)...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo ERREUR: Echec de l'installation des dependances
    pause
    exit /b 1
)
echo       Dependances OK

REM Lancer l'API
echo [3/3] Lancement du serveur API...
echo.
echo ===============================================
echo   API FastAPI - Ecoute sur TOUTES les interfaces (0.0.0.0:8000)
echo ===============================================
echo.
echo   Local:
echo     - http://localhost:8000
echo     - http://127.0.0.1:8000
echo.
echo   Externe (4G):
echo     - http://5.48.33.65:8000
echo.
echo   Documentation:
echo     - Swagger:  http://localhost:8000/docs
echo     - ReDoc:    http://localhost:8000/redoc
echo.
echo ===============================================
echo.
echo   Appuyez sur Ctrl+C pour arreter le serveur
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
