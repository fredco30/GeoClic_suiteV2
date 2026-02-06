@echo off
chcp 65001 >nul
title Configuration Pare-feu Windows - Geoclic

echo ╔══════════════════════════════════════════════════════════════╗
echo ║     CONFIGURATION PARE-FEU WINDOWS - GEOCLIC                 ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Vérifier les droits administrateur
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERREUR] Ce script nécessite les droits administrateur.
    echo.
    echo Faites un clic droit sur ce fichier et sélectionnez
    echo "Exécuter en tant qu'administrateur"
    echo.
    pause
    exit /b 1
)

echo [INFO] Ajout des règles de pare-feu pour Geoclic...
echo.

:: Port 3001 - PWA Mobile
echo [1/4] Port 3001 (PWA Mobile)...
netsh advfirewall firewall delete rule name="Geoclic PWA Mobile (3001)" >nul 2>&1
netsh advfirewall firewall add rule name="Geoclic PWA Mobile (3001)" dir=in action=allow protocol=tcp localport=3001
if %ERRORLEVEL% equ 0 (
    echo       [OK] Port 3001 autorisé
) else (
    echo       [ERREUR] Échec pour le port 3001
)

:: Port 3000 - Admin Web
echo [2/4] Port 3000 (Admin Web)...
netsh advfirewall firewall delete rule name="Geoclic Admin Web (3000)" >nul 2>&1
netsh advfirewall firewall add rule name="Geoclic Admin Web (3000)" dir=in action=allow protocol=tcp localport=3000
if %ERRORLEVEL% equ 0 (
    echo       [OK] Port 3000 autorisé
) else (
    echo       [ERREUR] Échec pour le port 3000
)

:: Port 8000 - API Backend
echo [3/4] Port 8000 (API Backend)...
netsh advfirewall firewall delete rule name="Geoclic API Backend (8000)" >nul 2>&1
netsh advfirewall firewall add rule name="Geoclic API Backend (8000)" dir=in action=allow protocol=tcp localport=8000
if %ERRORLEVEL% equ 0 (
    echo       [OK] Port 8000 autorisé
) else (
    echo       [ERREUR] Échec pour le port 8000
)

:: Port 5432 - PostgreSQL
echo [4/4] Port 5432 (PostgreSQL)...
netsh advfirewall firewall delete rule name="Geoclic PostgreSQL (5432)" >nul 2>&1
netsh advfirewall firewall add rule name="Geoclic PostgreSQL (5432)" dir=in action=allow protocol=tcp localport=5432
if %ERRORLEVEL% equ 0 (
    echo       [OK] Port 5432 autorisé
) else (
    echo       [ERREUR] Échec pour le port 5432
)

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  Configuration terminée !                                    ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║                                                              ║
echo ║  Ports autorisés:                                            ║
echo ║    - 3001 : PWA Mobile                                       ║
echo ║    - 3000 : Admin Web                                        ║
echo ║    - 8000 : API Backend                                      ║
echo ║    - 5432 : PostgreSQL                                       ║
echo ║                                                              ║
echo ║  Vous pouvez maintenant lancer launch_pwa.bat                ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
pause
