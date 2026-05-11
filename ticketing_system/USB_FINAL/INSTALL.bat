@echo off
:: ================================================================
:: INSTALL.bat - Installeur automatique SysMonAgent
:: Detecte Windows XP / 7 / 10 et installe la bonne version
:: EXECUTER EN TANT QU'ADMINISTRATEUR
:: ================================================================

setlocal EnableDelayedExpansion
title Installation SysMonAgent
color 0A

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║       SysMon Agent - Installation           ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: ─── Verifier droits admin ─────────────────────────────────────
net session >nul 2>&1
if errorlevel 1 (
    echo  [ERREUR] Droits administrateur requis !
    echo.
    echo  Fermez cette fenetre, puis :
    echo  Clic droit sur INSTALL.bat ^> "Executer en tant qu'administrateur"
    echo.
    pause
    exit /b 1
)

:: ─── Detecter la version de Windows ────────────────────────────
echo  [*] Detection du systeme...

set OS_VER=unknown
for /f "tokens=4-5 delims=. " %%i in ('ver') do set "OS_VER=%%i.%%j"

:: Windows XP = 5.1, Windows 7 = 6.1, Windows 10 = 10.0
echo  [*] Version detectee : %OS_VER%

set EXE_NAME=
set IS_XP=0

if "%OS_VER%"=="5.1" (
    echo  [*] Systeme : Windows XP
    set IS_XP=1
)
if "%OS_VER%"=="5.2" (
    echo  [*] Systeme : Windows XP x64 / Server 2003
    set IS_XP=1
)
if "%OS_VER%"=="6.1" (
    echo  [*] Systeme : Windows 7
    set EXE_NAME=SysMonAgent_Win7.exe
)
if "%OS_VER%"=="6.2" (
    echo  [*] Systeme : Windows 8
    set EXE_NAME=SysMonAgent_Win10.exe
)
if "%OS_VER%"=="6.3" (
    echo  [*] Systeme : Windows 8.1
    set EXE_NAME=SysMonAgent_Win10.exe
)
if "%OS_VER:~0,2%"=="10" (
    echo  [*] Systeme : Windows 10/11
    set EXE_NAME=SysMonAgent_Win10.exe
)

:: ─── Installation XP ───────────────────────────────────────────
if "%IS_XP%"=="1" goto INSTALL_XP

:: ─── Installation Win7 / Win10 ─────────────────────────────────
:INSTALL_WIN

if "%EXE_NAME%"=="" (
    echo  [ATTENTION] OS non reconnu, utilisation version Win10 par defaut.
    set EXE_NAME=SysMonAgent_Win10.exe
)

set "EXE_SRC=%~dp0%EXE_NAME%"
set "INSTALL_DIR=%SystemDrive%\SysMonAgent"
set "EXE_DEST=%INSTALL_DIR%\SysMonAgent.exe"

if not exist "%EXE_SRC%" (
    echo  [ERREUR] Fichier introuvable : %EXE_SRC%
    echo  Verifiez que tous les fichiers sont sur la cle USB.
    pause
    exit /b 1
)

echo  [1/4] Creation du dossier installation...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo  [2/4] Copie de l'executable...
copy /Y "%EXE_SRC%" "%EXE_DEST%" >nul

echo  [3/4] Suppression ancienne tache si existante...
schtasks /Delete /TN "SysMonAgent" /F >nul 2>&1

echo  [4/4] Creation de la tache planifiee (demarrage automatique)...
schtasks /Create ^
  /TN "SysMonAgent" ^
  /TR "\"%EXE_DEST%\"" ^
  /SC ONSTART ^
  /RU "SYSTEM" ^
  /RL HIGHEST ^
  /F ^
  /DELAY 0000:30 >nul

if errorlevel 1 (
    echo  [ERREUR] Impossible de creer la tache planifiee.
    echo  Essai methode alternative (registre)...
    reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" ^
        /v "SysMonAgent" /t REG_SZ /d "\"%EXE_DEST%\"" /f >nul
    echo  [OK] Agent ajoute au demarrage via registre.
) else (
    echo  [OK] Tache planifiee creee.
)

echo  [*] Demarrage immediat de l'agent...
start "" /B "%EXE_DEST%"

goto DONE

:: ─── Installation XP (batch natif) ────────────────────────────
:INSTALL_XP

set "BAT_SRC=%~dp0SysMonAgent_XP.bat"
set "VBS_SRC=%~dp0SysMonAgent_XP.vbs"
set "INSTALL_DIR=%SystemDrive%\SysMonAgent"

if not exist "%BAT_SRC%" (
    echo  [ERREUR] SysMonAgent_XP.bat introuvable.
    pause
    exit /b 1
)

echo  [1/3] Copie des fichiers...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy /Y "%BAT_SRC%" "%INSTALL_DIR%\SysMonAgent_XP.bat" >nul
copy /Y "%VBS_SRC%" "%INSTALL_DIR%\SysMonAgent_XP.vbs" >nul

echo  [2/3] Ajout au demarrage automatique...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" ^
    /v "SysMonAgent" ^
    /t REG_SZ ^
    /d "wscript.exe \"%INSTALL_DIR%\SysMonAgent_XP.vbs\"" ^
    /f >nul

echo  [3/3] Demarrage immediat...
start "" /B wscript.exe "%INSTALL_DIR%\SysMonAgent_XP.vbs"

goto DONE

:: ─── Fin ───────────────────────────────────────────────────────
:DONE
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║          INSTALLATION REUSSIE !              ║
echo  ╠══════════════════════════════════════════════╣
echo  ║                                              ║
echo  ║  L'agent tourne maintenant en arriere-plan   ║
echo  ║  Il redemarrera automatiquement avec Windows ║
echo  ║                                              ║
echo  ║  Logs : %%APPDATA%%\SysMonAgent\agent.log    ║
echo  ║  Dashboard : http://10.22.30.149:8888        ║
echo  ║                                              ║
echo  ║  Pour desinstaller : UNINSTALL.bat (admin)   ║
echo  ╚══════════════════════════════════════════════╝
echo.
pause
