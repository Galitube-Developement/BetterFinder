# BetterFinder - Installation

## Installation mit dem Installer

1. Kompiliere die Anwendung im Release-Modus
2. Installiere Inno Setup von https://jrsoftware.org/isdl.php
3. Das Icon liegt bereits im korrekten Format und Pfad:
   - Icon-Pfad: BetterFinder\Resources\BetterFinder-Icon.ico
   - Das Icon wird automatisch für den Installer verwendet
4. Öffne das Skript "BetterFinderInstaller.iss" mit Inno Setup
5. Klicke auf "Build" > "Compile" (oder drücke Strg+F9)
6. Der fertige Installer wird im Ordner "..\installer\" erstellt

## Umgang mit Antiviren-Warnungen

Es ist normal, dass selbst erstellte Installer manchmal als Bedrohung eingestuft werden (False Positive). Das liegt daran, dass sie nicht von einer bekannten Zertifizierungsstelle signiert sind.

Wenn der Installer eine Warnung auslöst:

1. **Temporär Antivirus deaktivieren:** Deaktiviere kurzzeitig dein Antivirenprogramm während der Installation
2. **Als Ausnahme hinzufügen:** Füge den Installer zu den Ausnahmen deines Antivirenprogramms hinzu
3. **Erweiterte Installation:** Bei Windows-Warnungen auf "Trotzdem ausführen" oder "Weitere Informationen" klicken
4. **Code-Signierung:** Für kommerzielle Anwendungen empfehlen wir die Anschaffung eines Code-Signierungszertifikats

Für maximale Sicherheit wurde der Installer mit der Option "PrivilegesRequired=lowest" erstellt, was bedeutet, dass keine Administratorrechte benötigt werden.

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