@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo        BetterFinder Installation
echo ===================================================
echo.

:: Erstelle temporäres Verzeichnis für Installationsdateien
set TEMPDIR=%TEMP%\betterfinder_install
echo Erstelle temporaeres Verzeichnis: %TEMPDIR%
if exist "%TEMPDIR%" rmdir /S /Q "%TEMPDIR%"
mkdir "%TEMPDIR%"
cd "%TEMPDIR%"

:: Prüfen, ob Python installiert ist und Version kontrollieren
echo Pruefe Python-Installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python wurde nicht gefunden!
    echo.
    echo Bitte installieren Sie Python 3.8 oder neuer von:
    echo https://www.python.org/downloads/
    echo.
    echo Stellen Sie sicher, dass Sie "Add Python to PATH" waehrend der Installation aktivieren.
    echo.
    echo Nach der Installation fuehren Sie diese Datei erneut aus.
    pause
    exit /B 1
) else (
    for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
    echo Python %PYTHON_VERSION% gefunden.
    
    :: Prüfen, ob Version mindestens 3.8 ist
    for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
        set MAJOR=%%a
        set MINOR=%%b
    )
    
    if %MAJOR% LSS 3 (
        echo Fehler: Python Version 3.8 oder neuer wird benoetigt!
        echo Die aktuelle Version ist %PYTHON_VERSION%
        echo.
        echo Bitte aktualisieren Sie Python und fuehren Sie die Installation erneut aus.
        pause
        exit /B 1
    ) else (
        if %MAJOR% EQU 3 (
            if %MINOR% LSS 8 (
                echo Fehler: Python Version 3.8 oder neuer wird benoetigt!
                echo Die aktuelle Version ist %PYTHON_VERSION%
                echo.
                echo Bitte aktualisieren Sie Python und fuehren Sie die Installation erneut aus.
                pause
                exit /B 1
            )
        )
    )
)

:: Prüfen, ob pip installiert ist
echo Pruefe pip-Installation...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo pip nicht gefunden, versuche es zu installieren...
    python -m ensurepip --default-pip
    if %errorlevel% neq 0 (
        echo Fehler bei der Installation von pip.
        echo Bitte installieren Sie pip manuell.
        pause
        exit /B 1
    )
)

:: Aktualisiere pip
echo Aktualisiere pip...
python -m pip install --upgrade pip

:: Bereinige alte Datenbank-Dateien
set DB_PATH=%USERPROFILE%\BetterFinder
echo Pruefe alte Datenbankdateien in %DB_PATH%...
if not exist "%DB_PATH%" (
    mkdir "%DB_PATH%"
) else (
    :: Beende eventuell laufende Python-Prozesse
    taskkill /F /IM python.exe >NUL 2>&1
    
    :: Warte kurz, damit Prozesse beendet werden können
    timeout /t 2 /nobreak >NUL
    
    :: Lösche alte Datenbankdateien
    if exist "%DB_PATH%\index.db" (
        echo Alte Datenbank gefunden. Sichere und bereinige...
        if exist "%DB_PATH%\index.db.bak" del /F /Q "%DB_PATH%\index.db.bak"
        copy "%DB_PATH%\index.db" "%DB_PATH%\index.db.bak" >nul 2>&1
        del /F /Q "%DB_PATH%\index.db" >nul 2>&1
    )
    if exist "%DB_PATH%\index.db-wal" del /F /Q "%DB_PATH%\index.db-wal" >nul 2>&1
    if exist "%DB_PATH%\index.db-shm" del /F /Q "%DB_PATH%\index.db-shm" >nul 2>&1
)

:: Installiere benötigte Python-Pakete
echo Installiere benoetigte Python-Pakete...
python -m pip install -r requirements.txt

:: Falls die Installation fehlschlägt, versuche einzelne wichtige Pakete zu installieren
if %errorlevel% neq 0 (
    echo Versuche einzelne Installation der kritischen Komponenten...
    python -m pip install PyQt5==5.15.9
    python -m pip install pywin32==306
    python -m pip install pillow==10.0.0
    python -m pip install pyinstaller==5.13.0
    python -m pip install pytest==7.4.0
    python -m pip install sqlite-utils==3.35.1
)

:: Erstelle ausführbare Datei mit PyInstaller
echo.
echo Erstelle ausfuehrbare Datei...
python -m PyInstaller --name=BetterFinder --windowed --clean --add-data "app/resources;app/resources" --icon=app/resources/icon.ico app/main.py

:: Überprüfe, ob die EXE-Datei erstellt wurde
if not exist "dist\BetterFinder\BetterFinder.exe" (
    echo Fehler beim Erstellen der ausfuehrbaren Datei!
    echo Versuche alternative Methode...
    
    :: Versuche es mit einer einfacheren PyInstaller-Konfiguration
    python -m PyInstaller --name=BetterFinder --onefile --windowed app/main.py
    
    if not exist "dist\BetterFinder.exe" (
        echo Konnte keine ausfuehrbare Datei erstellen.
        echo BetterFinder kann trotzdem mit der run.bat-Datei ausgefuehrt werden.
    ) else (
        :: Verschiebe die Datei in das Installationsverzeichnis
        if not exist "%USERPROFILE%\BetterFinder\bin" mkdir "%USERPROFILE%\BetterFinder\bin"
        copy "dist\BetterFinder.exe" "%USERPROFILE%\BetterFinder\bin\" >nul 2>&1
        echo EXE-Datei wurde im Verzeichnis "%USERPROFILE%\BetterFinder\bin" installiert.
    )
) else (
    :: Verschiebe die Dateien in das Installationsverzeichnis
    if not exist "%USERPROFILE%\BetterFinder\bin" mkdir "%USERPROFILE%\BetterFinder\bin"
    echo Kopiere Dateien ins Zielverzeichnis...
    xcopy "dist\BetterFinder\*" "%USERPROFILE%\BetterFinder\bin\" /E /I /Y >nul 2>&1
    echo BetterFinder wurde im Verzeichnis "%USERPROFILE%\BetterFinder\bin" installiert.
)

:: Erstelle Desktop-Verknüpfungen
echo Erstelle Desktop-Verknuepfungen...
set DESKTOP=%USERPROFILE%\Desktop

:: Verknüpfung für die EXE-Datei (falls vorhanden)
if exist "%USERPROFILE%\BetterFinder\bin\BetterFinder.exe" (
    echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
    echo sLinkFile = "%DESKTOP%\BetterFinder.lnk" >> CreateShortcut.vbs
    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
    echo oLink.TargetPath = "%USERPROFILE%\BetterFinder\bin\BetterFinder.exe" >> CreateShortcut.vbs
    echo oLink.IconLocation = "%USERPROFILE%\BetterFinder\bin\BetterFinder.exe" >> CreateShortcut.vbs
    echo oLink.Save >> CreateShortcut.vbs
    cscript /nologo CreateShortcut.vbs
    del CreateShortcut.vbs
    echo Desktop-Verknuepfung fuer BetterFinder.exe erstellt.
)

:: Verknüpfung für die BAT-Datei (als Fallback)
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateBatShortcut.vbs
echo sLinkFile = "%DESKTOP%\BetterFinder (Python).lnk" >> CreateBatShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateBatShortcut.vbs
echo oLink.TargetPath = "%~dp0run.bat" >> CreateBatShortcut.vbs
echo oLink.WorkingDirectory = "%~dp0" >> CreateBatShortcut.vbs
echo oLink.IconLocation = "%SystemRoot%\System32\SHELL32.dll,13" >> CreateBatShortcut.vbs
echo oLink.Save >> CreateBatShortcut.vbs
cscript /nologo CreateBatShortcut.vbs
del CreateBatShortcut.vbs
echo Desktop-Verknuepfung fuer run.bat erstellt.

:: Bereinige temporäre Dateien
echo.
echo Bereinige temporaere Dateien...
cd %~dp0
if exist "%TEMPDIR%" rmdir /S /Q "%TEMPDIR%"

echo.
echo ===================================================
echo      BetterFinder wurde erfolgreich installiert!
echo ===================================================
echo.
echo Sie koennen BetterFinder jetzt auf eine der folgenden Arten starten:
echo.
echo 1. Klicken Sie auf die Desktop-Verknuepfung "BetterFinder"
echo 2. Wenn die EXE nicht funktioniert, nutzen Sie "BetterFinder (Python)"
echo.
echo Viel Spass bei der Nutzung von BetterFinder!
echo.
pause 