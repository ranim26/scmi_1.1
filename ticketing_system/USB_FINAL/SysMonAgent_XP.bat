@echo off
:: ================================================================
:: SysMonAgent_XP.bat - Agent natif Windows XP
:: Utilise uniquement des outils Windows integres (wmic, systeminfo)
:: Aucune installation requise
:: ================================================================

setlocal EnableDelayedExpansion

set SERVER=10.22.30.149
set PORT=8888
set INTERVAL=30
set AGENT_NAME=%COMPUTERNAME%

:: Dossier de travail et logs
set "WORK_DIR=%APPDATA%\SysMonAgent"
if not exist "%WORK_DIR%" mkdir "%WORK_DIR%"
set "LOG=%WORK_DIR%\agent.log"
set "TMP_JSON=%WORK_DIR%\packet.json"
set "TMP_VBS=%WORK_DIR%\send.vbs"

call :LOG "=== SysMonAgent XP demarre | Machine: %AGENT_NAME% | Serveur: %SERVER%:%PORT% ==="

:LOOP
    call :COLLECT_AND_SEND
    :: Attendre INTERVAL secondes
    ping -n %INTERVAL% 127.0.0.1 >nul 2>&1
goto LOOP

:: ─── Collecte et envoi ─────────────────────────────────────────
:COLLECT_AND_SEND
    set "NOW="
    for /f "tokens=1-2 delims=T" %%a in ('wmic os get LocalDateTime /value ^| find "="') do (
        set "DT=%%b"
    )
    for /f "tokens=* delims=" %%a in ('wmic os get LocalDateTime /value') do (
        set "%%a" 2>nul
    )
    set "TIMESTAMP=%LocalDateTime:~0,4%-%LocalDateTime:~4,2%-%LocalDateTime:~6,2%T%LocalDateTime:~8,2%:%LocalDateTime:~10,2%:%LocalDateTime:~12,2%Z"

    :: CPU
    set CPU_LOAD=0
    for /f "skip=1 tokens=2 delims=," %%a in ('wmic cpu get LoadPercentage /format:csv 2^>nul') do (
        if not "%%a"=="" set CPU_LOAD=%%a
    )
    set CPU_LOAD=!CPU_LOAD: =!

    :: CPU Name
    set CPU_NAME=Unknown
    for /f "skip=1 delims=" %%a in ('wmic cpu get Name 2^>nul') do (
        if not "%%a"=="" if "!CPU_NAME!"=="Unknown" set "CPU_NAME=%%a"
    )

    :: RAM
    set RAM_TOTAL=0
    set RAM_FREE=0
    for /f "skip=1 tokens=2 delims=," %%a in ('wmic os get TotalVisibleMemorySize /format:csv 2^>nul') do (
        if not "%%a"=="" set RAM_TOTAL=%%a
    )
    for /f "skip=1 tokens=2 delims=," %%a in ('wmic os get FreePhysicalMemory /format:csv 2^>nul') do (
        if not "%%a"=="" set RAM_FREE=%%a
    )
    set RAM_TOTAL=!RAM_TOTAL: =!
    set RAM_FREE=!RAM_FREE: =!

    :: Calculer RAM utilisee en MB (approximatif)
    set /a RAM_TOTAL_MB=!RAM_TOTAL! / 1024 2>nul
    set /a RAM_FREE_MB=!RAM_FREE! / 1024 2>nul
    set /a RAM_USED_MB=!RAM_TOTAL_MB! - !RAM_FREE_MB! 2>nul

    :: Disque C:
    set DISK_FREE=0
    set DISK_TOTAL=0
    for /f "skip=1 tokens=2,3 delims=," %%a in ('wmic logicaldisk where "DeviceID='C:'" get FreeSpace^,Size /format:csv 2^>nul') do (
        if not "%%a"=="" set DISK_FREE=%%a
        if not "%%b"=="" set DISK_TOTAL=%%b
    )

    :: OS
    set OS_NAME=Windows XP
    for /f "skip=1 delims=" %%a in ('wmic os get Caption 2^>nul') do (
        if not "%%a"=="" if "!OS_NAME!"=="Windows XP" set "OS_NAME=%%a"
    )

    :: Construire JSON
    set SEQ=0
    if exist "%WORK_DIR%\seq.txt" (
        set /p SEQ=<"%WORK_DIR%\seq.txt"
        set /a SEQ=!SEQ!+1
    )
    echo !SEQ!>"%WORK_DIR%\seq.txt"

    (
        echo {
        echo   "protocol": "SYSMON_V1",
        echo   "version": "1.0.0",
        echo   "agent_id": "xp-%COMPUTERNAME%",
        echo   "agent_name": "%AGENT_NAME%",
        echo   "timestamp": "%TIMESTAMP%",
        echo   "sequence": !SEQ!,
        echo   "payload": {
        echo     "system": {
        echo       "os": "Windows",
        echo       "os_release": "XP",
        echo       "hostname": "%COMPUTERNAME%",
        echo       "processor": "!CPU_NAME!"
        echo     },
        echo     "cpu": {
        echo       "usage_percent": !CPU_LOAD!
        echo     },
        echo     "memory": {
        echo       "ram_total_mb": !RAM_TOTAL_MB!,
        echo       "ram_free_mb": !RAM_FREE_MB!,
        echo       "ram_used_mb": !RAM_USED_MB!
        echo     },
        echo     "disks": [
        echo       {
        echo         "device": "C:",
        echo         "disk_free_bytes": !DISK_FREE!,
        echo         "disk_total_bytes": !DISK_TOTAL!
        echo       }
        echo     ],
        echo     "network": {},
        echo     "processes": []
        echo   }
        echo }
    ) > "%TMP_JSON%"

    :: Envoyer via VBScript (HTTP POST natif Windows XP)
    call :WRITE_VBS
    cscript //nologo "%TMP_VBS%" >nul 2>&1

    if errorlevel 1 (
        call :LOG "Erreur envoi paquet #!SEQ!"
    ) else (
        call :LOG "Paquet #!SEQ! envoye | CPU: !CPU_LOAD!%% | RAM: !RAM_USED_MB!MB / !RAM_TOTAL_MB!MB"
    )
exit /b

:: ─── Ecrire le VBScript d'envoi HTTP ──────────────────────────
:WRITE_VBS
    (
        echo Dim fso, ts, json
        echo Set fso = CreateObject^("Scripting.FileSystemObject"^)
        echo Set ts = fso.OpenTextFile^("%TMP_JSON:\=\\%", 1^)
        echo json = ts.ReadAll
        echo ts.Close
        echo.
        echo Dim http
        echo Set http = CreateObject^("MSXML2.ServerXMLHTTP"^)
        echo http.Open "POST", "http://%SERVER%:%PORT%/api/report", False
        echo http.setRequestHeader "Content-Type", "application/json"
        echo http.setRequestHeader "X-Protocol", "SYSMON_V1"
        echo http.setRequestHeader "X-Agent-Name", "%AGENT_NAME%"
        echo http.Send json
        echo.
        echo If http.Status ^<^> 200 Then
        echo   WScript.Quit 1
        echo End If
    ) > "%TMP_VBS%"
exit /b

:: ─── Log ───────────────────────────────────────────────────────
:LOG
    set "MSG=%~1"
    echo [%date% %time:~0,8%] %MSG% >> "%LOG%"
exit /b
