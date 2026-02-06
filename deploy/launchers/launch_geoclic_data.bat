@echo off
REM ============================================
REM GéoClic Data - Lanceur Admin Web
REM ============================================
REM Ce script lance l'interface d'administration web
REM ============================================

echo.
echo ========================================
echo   GéoClic Data - Admin Web
echo ========================================
echo.

REM Vérifier que Docker est lancé
echo [1/4] Verification de Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Docker n'est pas lance. Veuillez demarrer Docker Desktop.
    pause
    exit /b 1
)
echo       Docker OK

REM Vérifier que le container PostgreSQL tourne
echo [2/4] Verification du container PostgreSQL...
docker start geoclic_server_v14 >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Container geoclic_server_v14 introuvable.
    echo        Creez-le avec: docker run -d --name geoclic_server_v14 -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgis/postgis:16-3.4
    pause
    exit /b 1
)
echo       PostgreSQL OK

REM Lancer l'API FastAPI
echo [3/4] Lancement de l'API FastAPI (port 8000)...
cd /d "%~dp0api"
start "GéoClic API" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

REM Attendre que l'API démarre
echo       Attente demarrage API (3 secondes)...
timeout /t 3 /nobreak >nul
echo       API lancee sur http://localhost:8000

REM Lancer GéoClic Data (Vue.js)
echo [4/4] Lancement de GéoClic Data (Vue.js)...
cd /d "%~dp0geoclic_data"

REM Vérifier que Node.js est installé
echo       Verification de Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Node.js n'est pas installe ou pas dans le PATH
    echo        Telechargez Node.js sur https://nodejs.org/
    pause
    exit /b 1
)
echo       Node.js OK

REM Vérifier si node_modules existe, sinon installer
if not exist "node_modules" (
    echo       Installation des dependances npm...
    call npm install
    if errorlevel 1 (
        echo ERREUR: npm install a echoue
        pause
        exit /b 1
    )
    echo       Dependances installees
)

REM Lancer Vite avec --host explicite pour écouter sur toutes les interfaces
echo       Demarrage du serveur Vite...
start "GéoClic Data - Vue.js" cmd /k "npm run dev -- --host 0.0.0.0"

echo.
echo ========================================
echo   GéoClic Data lance !
echo ========================================
echo.
echo   === ACCES LOCAL ===
echo   API:        http://localhost:8000
echo   API Docs:   http://localhost:8000/docs
echo   Admin Web:  http://localhost:3000
echo.
echo   === ACCES RESEAU (autres appareils) ===
echo   Votre IP locale:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do @echo     %%a
echo.
echo   Remplacez localhost par votre IP ci-dessus
echo   Ex: http://192.168.1.x:3000
echo.
echo   === CREDENTIALS ===
echo   Email: admin@geoclic.local
echo   Password: admin123
echo.
echo   Pour arreter: fermez les fenetres CMD
echo ========================================
echo.
pause
