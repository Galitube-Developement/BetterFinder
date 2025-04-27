# BetterFinder

BetterFinder ist ein leistungsstarkes Dateisuche-Programm, das eine schnelle Indizierung des Dateisystems ermöglicht und nahezu sofortige Suchergebnisse liefert.

## Hauptfunktionen

- Blitzschnelle Dateisystem-Indizierung
- Sofortige Suchergebnisse während der Eingabe
- Erweiterte Suchoperatoren (AND, OR, NOT, Platzhalter)
- Dateitypfilterung
- Suchverlauf und Dateiwiederherstellung
- Netzwerksuche für freigegebene Laufwerke
- Windows Explorer-Integration
- Kommandozeilenunterstützung

## Installation

*Installationsanweisungen folgen*

## Entwicklung

BetterFinder wird mit Python und Qt für die Benutzeroberfläche entwickelt.

## Lizenz

Siehe [LICENSE.md](LICENSE.md) für Lizenzinformationen.

## Funktionen

- Schnelle Indizierung aller Dateien auf allen Festplattenlaufwerken
- Sofortige Suche nach Dateinamen und Pfaden
- Filterung nach Dateierweiterungen
- Suche in Dateiinhalten mit der `content:` Syntax
- Echtzeit-Aktualisierung des Index durch NTFS USN Journal
- Dunkles Design mit moderner Benutzeroberfläche

## Voraussetzungen

- Windows 10/11
- .NET 6.0 oder höher

## Verwendung

Nach dem Start der Anwendung wird automatisch eine Indizierung aller Festplattenlaufwerke gestartet. Nach Abschluss der Indizierung kann die Suchleiste verwendet werden, um schnell nach Dateien zu suchen.

### Suchfunktionen

- Einfache Suche: Geben Sie einen Teil des Dateinamens ein
- Erweiterungssuche: Suchen Sie nach Dateien mit einer bestimmten Erweiterung (z.B. ".txt")
- Inhaltssuche: Verwenden Sie `content:` gefolgt vom Suchbegriff, um in Dateiinhalten zu suchen

## Everything vs. BetterFinder

Wie das Original-Everything bietet BetterFinder:

- Schnelle Indizierung von Dateien und Ordnern
- Echtzeit-Updates durch NTFS USN Journal
- Geringe Ressourcennutzung
- Inhaltssuche für Textdateien

## Leistung und Ressourcen

- Schnelle Indizierung (wenige Sekunden bis Minuten)
- Geringe Speichernutzung
- Echtzeit-Aktualisierung des Index
- NTFS USN Journal sorgt dafür, dass keine Änderungen verpasst werden, auch wenn BetterFinder nicht läuft
