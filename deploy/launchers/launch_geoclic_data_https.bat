@echo off
chcp 65001 >nul
title Geoclic Data - HTTPS avec Cloudflare

echo ╔══════════════════════════════════════════════════════════════╗
echo ║       GEOCLIC DATA - Acces externe HTTPS                    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Verifier Node.js
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERREUR] Node.js n'est pas installe.
    pause
    exit /b 1
)
echo [OK] Node.js trouve

:: Verifier Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERREUR] Python n'est pas installe.
    pause
    exit /b 1
)
echo [OK] Python trouve

:: Verifier cloudflared
set CLOUDFLARED_PATH=%~dp0geoclic_mobile_pwa\cloudflared.exe
if not exist "%CLOUDFLARED_PATH%" (
    echo.
    echo [INFO] Telechargement de cloudflared...
    cd /d "%~dp0geoclic_mobile_pwa"
    curl -L -o cloudflared.exe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
)
echo [OK] cloudflared trouve

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  Demarrage des services...                                   ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Lancer l'API en arriere-plan
echo [1/3] Demarrage de l'API...
cd /d "%~dp0api"
start "Geoclic API" cmd /c "python -m uvicorn main:app --host 0.0.0.0 --port 8000"
timeout /t 3 >nul

:: Lancer geoclic_data en arriere-plan
echo [2/3] Demarrage de Geoclic Data...
cd /d "%~dp0geoclic_data"
if not exist "node_modules" (
    echo     Installation des dependances...
    call npm install
)
start "Geoclic Data" cmd /c "npm run dev"
timeout /t 5 >nul

:: Lancer Cloudflare Tunnel
echo [3/3] Demarrage du tunnel HTTPS (Cloudflare)...
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  IMPORTANT - Copiez l'URL HTTPS affichee ci-dessous !       ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║                                                              ║
echo ║  L'URL sera du type: https://xxxxx.trycloudflare.com        ║
echo ║                                                              ║
echo ║  Utilisez cette URL pour acceder a Geoclic Data             ║
echo ║  depuis n'importe ou !                                       ║
echo ║                                                              ║
echo ║  Appuyez sur Ctrl+C pour tout arreter                       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

"%CLOUDFLARED_PATH%" tunnel --url http://localhost:3000 --protocol http2

:: Nettoyage
echo.
echo Arret des services...
taskkill /FI "WINDOWTITLE eq Geoclic API" >nul 2>&1
taskkill /FI "WINDOWTITLE eq Geoclic Data" >nul 2>&1
echo Termine.
pause
