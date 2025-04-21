# BetterFinder

BetterFinder ist eine Windows-Anwendung zur schnellen Dateisuche auf allen Laufwerken, ähnlich dem Programm "Everything". Die Anwendung bietet eine benutzerfreundliche Oberfläche mit einer dunklen Suchleiste und schneller Indizierung aller Dateien.

## Funktionen

- Schnelle Indizierung aller Dateien auf allen Festplattenlaufwerken
- Sofortige Suche nach Dateinamen und Pfaden
- Filterung nach Dateierweiterungen
- Dunkles Design mit moderner Benutzeroberfläche

## Voraussetzungen

- Windows 10/11
- .NET 6.0 oder höher

## Entwicklung

Das Projekt wurde mit Visual Studio erstellt und verwendet WPF für die Benutzeroberfläche.

Um das Projekt zu bauen:

```powershell
cd src/BetterFinder
dotnet build
```

## Verwendung

Nach dem Start der Anwendung wird automatisch eine Indizierung aller Festplattenlaufwerke gestartet. Nach Abschluss der Indizierung kann die Suchleiste verwendet werden, um schnell nach Dateien zu suchen.

### Suchfunktionen

- Einfache Suche: Geben Sie einen Teil des Dateinamens ein
- Erweiterungssuche: Suchen Sie nach Dateien mit einer bestimmten Erweiterung (z.B. ".txt")
