@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   BetterFinder Installer-Erstellung
echo ===================================================

REM Überprüfe, ob Inno Setup installiert ist
where iscc >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Inno Setup wurde nicht gefunden!
    echo Bitte installiere Inno Setup von https://jrsoftware.org/isdl.php
    echo Nach der Installation starte dieses Skript erneut.
    pause
    exit /b 1
)

REM Überprüfe, ob die EXE-Datei existiert
if not exist "dist\BetterFinder.exe" (
    echo Die BetterFinder.exe wurde nicht im Verzeichnis 'dist' gefunden!
    echo Bitte führe zuerst 'python build_exe.py' aus, um die EXE zu erstellen.
    pause
    exit /b 1
)

REM Erstelle Verzeichnisse, falls sie nicht existieren
if not exist "installer" mkdir installer
if not exist "installer_assets" mkdir installer_assets

REM Prüfe, ob die Bilddateien für den Installer existieren
set missing_images=0
if not exist "installer_assets\wizard-image.bmp" (
    echo HINWEIS: Die Datei installer_assets\wizard-image.bmp fehlt.
    echo         Ein Standard-Bild wird verwendet.
    echo         Für ein individuelles Bild erstelle eine BMP-Datei (164x314 Pixel) und
    echo         speichere sie als "installer_assets\wizard-image.bmp"
    set missing_images=1
)

if not exist "installer_assets\wizard-small-image.bmp" (
    echo HINWEIS: Die Datei installer_assets\wizard-small-image.bmp fehlt.
    echo         Ein Standard-Bild wird verwendet.
    echo         Für ein individuelles Bild erstelle eine BMP-Datei (55x58 Pixel) und
    echo         speichere sie als "installer_assets\wizard-small-image.bmp"
    set missing_images=1
)

REM Kompiliere den Installer mit Inno Setup
echo.
echo Starte die Erstellung des Installers mit Inno Setup...
iscc /Q "setup_script.iss"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Bei der Erstellung des Installers ist ein Fehler aufgetreten!
    pause
    exit /b 1
)

echo.
echo Der Installer wurde erfolgreich erstellt!
echo Installer-Datei: %CD%\installer\BetterFinder_Setup_1.0.exe

if %missing_images% EQU 1 (
    echo.
    echo HINWEIS: Für einen individuelleren Installer könntest du eigene Bilder erstellen:
    echo - installer_assets\wizard-image.bmp (164x314 Pixel) für die linke Seite
    echo - installer_assets\wizard-small-image.bmp (55x58 Pixel) für die obere rechte Ecke
)

echo.
echo ===================================================
pause 