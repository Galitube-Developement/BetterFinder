=============================================
BetterFinder Installer-Erstellung - Anleitung
=============================================

Diese Readme-Datei erklärt, wie du einen professionellen Installer für BetterFinder mit Inno Setup erstellst.

Voraussetzungen:
---------------
1. Die fertige BetterFinder.exe wurde mit PyInstaller erstellt (liegt im "dist"-Verzeichnis)
2. Inno Setup ist installiert (Download: https://jrsoftware.org/isdl.php)

Installationsschritte für Inno Setup:
------------------------------------
1. Besuche https://jrsoftware.org/isdl.php
2. Lade die neueste Version von Inno Setup herunter
3. Führe die heruntergeladene Datei aus und folge den Anweisungen
4. Wähle bei der Installation die Option "Inno Setup Preprocessor" aus

Erstellen des Installers:
------------------------
1. Stelle sicher, dass die "BetterFinder.exe" im Verzeichnis "dist" liegt
2. Erstelle Bilddateien für den Installer (optional):
   - wizard-image.bmp (164x314 Pixel) für die linke Seite des Installers
   - wizard-small-image.bmp (55x58 Pixel) für die obere rechte Ecke
   - Speichere diese im "installer_assets"-Verzeichnis
3. Öffne "setup_script.iss" mit Inno Setup Compiler
4. Klicke auf "Kompilieren" (oder drücke F9)
5. Der Installer wird im "installer"-Verzeichnis erstellt

Der fertige Installer bietet:
---------------------------
- Professionelles Erscheinungsbild
- Auswahl des Installationsverzeichnisses
- Optionen für:
  * Desktop-Symbol erstellen
  * Startmenü-Eintrag erstellen
  * Autostart aktivieren
- Kontextmenüeintrag für Ordner
- Mehrsprachige Unterstützung (Deutsch/Englisch)
- Automatische Erkennung der Systemkompatibilität
- Saubere Deinstallation mit Option zum Löschen von Benutzereinstellungen

Anpassungen:
-----------
Du kannst folgende Aspekte des Installers anpassen:
1. Version und Herausgeber in den #define-Anweisungen am Anfang der .iss-Datei
2. Standardinstallationsverzeichnis in DefaultDirName
3. Layout und Design durch Ändern der WizardImageFile und WizardSmallImageFile
4. Unterstützte Sprachen im [Languages]-Abschnitt
5. Standardmäßig aktivierte Optionen durch Ändern der Flags in [Tasks]

Bei Fragen oder Problemen kontaktiere das BetterFinder-Team. 