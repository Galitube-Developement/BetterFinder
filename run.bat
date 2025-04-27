@echo off
echo ===================================================
echo        BetterFinder wird gestartet...
echo ===================================================
echo.

:: Bereinigung von eventuell laufenden Python-Prozessen
echo Pruefe laufende Python-Prozesse...
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo Beende laufende Python-Prozesse...
    taskkill /F /IM python.exe >NUL 2>&1
    timeout /t 2 /nobreak >NUL
)

:: Prüfen, ob Python installiert ist
echo Pruefe Python-Installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python wurde nicht gefunden!
    echo.
    echo Bitte Python 3.8 oder neuer installieren und installer.bat ausfuehren.
    echo.
    pause
    exit /B 1
) else (
    for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
    echo Python %PYTHON_VERSION% gefunden.
)

:: Prüfen, ob die Abhängigkeiten installiert sind
echo Pruefe Abhaengigkeiten...
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo PyQt5 nicht installiert! Installiere Abhaengigkeiten...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Versuche einzelne Installation der kritischen Komponenten...
        python -m pip install PyQt5==5.15.9
        python -m pip install pywin32==306
        if %errorlevel% neq 0 (
            echo Fehler bei der Installation der Abhaengigkeiten.
            echo Fuehren Sie bitte 'installer.bat' aus, um alle Abhaengigkeiten zu installieren.
            pause
            exit /B 1
        )
    )
)

:: Prüfen, ob alte Datenbank gesperrt ist und ggf. bereinigen
echo Pruefe alte Datenbankdateien...
set DB_PATH=%USERPROFILE%\BetterFinder
if exist "%DB_PATH%\index.db" (
    echo Stelle sicher, dass Datenbank nicht gesperrt ist...
    :: Versuche, die WAL-Datei zu löschen, falls vorhanden
    if exist "%DB_PATH%\index.db-wal" (
        del /F /Q "%DB_PATH%\index.db-wal" >nul 2>&1
        if exist "%DB_PATH%\index.db-wal" (
            echo Warnung: Konnte WAL-Datei nicht loeschen, Datenbank koennte gesperrt sein.
        ) else (
            echo WAL-Datei erfolgreich entfernt.
        )
    )
    if exist "%DB_PATH%\index.db-shm" (
        del /F /Q "%DB_PATH%\index.db-shm" >nul 2>&1
        if exist "%DB_PATH%\index.db-shm" (
            echo Warnung: Konnte SHM-Datei nicht loeschen, Datenbank koennte gesperrt sein.
        ) else (
            echo SHM-Datei erfolgreich entfernt.
        )
    )
    
    :: Optional: Bei häufigen Problemen mit der Datenbank, Sicherung erstellen
    if not exist "%DB_PATH%\index.db.bak" (
        echo Erstelle Sicherung der Datenbank...
        copy "%DB_PATH%\index.db" "%DB_PATH%\index.db.bak" >nul 2>&1
    )
)

:: Programm starten
echo.
echo ===================================================
echo Starte BetterFinder...
echo ===================================================
python -m app.main

:: Fehlerbehandlung
if %errorlevel% neq 0 (
    echo.
    echo BetterFinder wurde mit einem Fehler beendet (Code: %errorlevel%).
    echo.
    echo Moegliche Loesungen bei Problemen:
    echo.
    echo 1. Stellen Sie sicher, dass keine andere Instanz von BetterFinder laeuft.
    echo 2. Bei Datenbankproblemen, versuchen Sie:
    echo    a) Entfernen der Datenbankdatei:
    echo       del "%USERPROFILE%\BetterFinder\index.db"
    echo    b) Wiederherstellen der Sicherung (falls vorhanden):
    echo       copy "%USERPROFILE%\BetterFinder\index.db.bak" "%USERPROFILE%\BetterFinder\index.db"
    echo 3. Führen Sie 'installer.bat' erneut aus, um alle Komponenten zu aktualisieren.
    echo.
    
    choice /C JN /M "Moechten Sie die Datenbank zuruecksetzen (J/N)? "
    if %errorlevel% equ 1 (
        echo Setze Datenbank zurueck...
        if exist "%DB_PATH%\index.db" del /F /Q "%DB_PATH%\index.db"
        if exist "%DB_PATH%\index.db-wal" del /F /Q "%DB_PATH%\index.db-wal"
        if exist "%DB_PATH%\index.db-shm" del /F /Q "%DB_PATH%\index.db-shm"
        echo Datenbank wurde zurueckgesetzt. Starten Sie BetterFinder neu.
    )
    
    pause
) 