# Installation von BetterFinder

## Voraussetzungen

- Windows 10 oder neuer
- Python 3.8 oder neuer
- pip (Python-Paketmanager)

## Installation

1. **Python-Abhängigkeiten installieren:**

   ```
   pip install -r requirements.txt
   ```

2. **Programm starten:**

   ```
   python -m app.main
   ```

## Alternativ: Ausführbare Datei erstellen

Sie können eine eigenständige .exe-Datei erstellen:

1. **PyInstaller installieren:**

   ```
   pip install pyinstaller
   ```

2. **Ausführbare Datei erstellen:**

   ```
   pyinstaller --onefile --windowed --icon=BetterFinder-Icon.png --add-data "BetterFinder-Icon.png;." --name BetterFinder app/main.py
   ```

3. **Die erstellte .exe-Datei finden:**

   Nach Abschluss des Vorgangs finden Sie die BetterFinder.exe im Verzeichnis "dist".

## Verwendung

1. **Starten Sie BetterFinder**
2. **Warten Sie, bis die Indizierung abgeschlossen ist**
3. **Geben Sie den Suchbegriff ein und sehen Sie sofortige Ergebnisse**

## Features

- Schnelle Dateisystem-Indizierung
- Sofortige Suchergebnisse
- Unterstützung für erweiterte Suchoperatoren (AND, OR, NOT)
- Platzhaltersuche mit * und ?
- Reguläre Ausdrücke mit Präfix "regex:"
- Dateitypfilterung 