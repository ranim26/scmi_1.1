@echo off
:: ================================================================
:: UNINSTALL.bat - Desinstalle SysMonAgent (toutes versions)
:: EXECUTER EN TANT QU'ADMINISTRATEUR
:: ================================================================

net session >nul 2>&1
if errorlevel 1 (
    echo Executer en tant qu'Administrateur svp.
    pause
    exit /b 1
)

echo Desinstallation de SysMonAgent...

:: Arreter le processus
taskkill /IM SysMonAgent.exe /F >nul 2>&1
taskkill /IM SysMonAgent_Win10.exe /F >nul 2>&1
taskkill /IM SysMonAgent_Win7.exe /F >nul 2>&1

:: Supprimer la tache planifiee (Win7/10)
schtasks /End    /TN "SysMonAgent" >nul 2>&1
schtasks /Delete /TN "SysMonAgent" /F >nul 2>&1

:: Supprimer la cle registre (XP / fallback)
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "SysMonAgent" /f >nul 2>&1

:: Supprimer les fichiers
if exist "%SystemDrive%\SysMonAgent" rmdir /S /Q "%SystemDrive%\SysMonAgent"

echo.
echo SysMonAgent desinstalle avec succes.
pause
