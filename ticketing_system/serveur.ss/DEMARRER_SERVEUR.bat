@echo off
:: ================================================================
:: DEMARRER_SERVEUR.bat
:: Lance le serveur SysMon sur VOTRE PC
:: Double-clic pour démarrer
:: ================================================================
title SysMon Server
color 0A

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║         SysMon - Demarrage Serveur          ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: Installer les dépendances si nécessaire
echo [*] Verification des dependances...
pip install flask flask-socketio --quiet
echo [OK] Dependances pres
echo.

echo [*] Demarrage du serveur...
echo.
echo  Dashboard disponible sur :
echo  http://localhost:8888
echo  http://10.22.30.149:8888  (depuis les autres machines)
echo.
echo  Ctrl+C pour arreter le serveur
echo.

python server.py

pause
