# BetterFinder - Installation

## Installation mit dem Installer

1. Kompiliere die Anwendung im Release-Modus
2. Installiere Inno Setup von https://jrsoftware.org/isdl.php
3. Öffne das Skript "BetterFinderInstaller.iss" mit Inno Setup
4. Klicke auf "Build" > "Compile" (oder drücke Strg+F9)
5. Der fertige Installer wird im Ordner "..\installer\" erstellt

## Manuelle Installation

Alternativ kannst du die Anwendung auch manuell installieren:

1. Kompiliere die Anwendung im Release-Modus
2. Kopiere den Inhalt des Ordners "bin\Release\net6.0-windows" in einen beliebigen Ordner
3. Erstelle eine Verknüpfung zu BetterFinder.exe im Startmenü oder auf dem Desktop

## Anmerkungen zur Installation

- Der Installer erstellt automatisch Einträge im Startmenü
- Die Option zur Desktop-Verknüpfung kann während der Installation ausgewählt werden
- Eine Deinstallation ist über die Systemsteuerung (Programme und Features) möglich

## Systemvoraussetzungen

- Windows 10 oder neuer
- .NET 6.0 Runtime 