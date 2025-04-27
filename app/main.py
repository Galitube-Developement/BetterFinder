"""
Haupteinstiegspunkt für BetterFinder

Dieses Modul startet die Anwendung und initialisiert alle erforderlichen Komponenten.
"""

import sys
import os
import argparse
from PyQt5.QtWidgets import QApplication

from app.gui.main_window import MainWindow


def parse_arguments():
    """
    Parst Kommandozeilenargumente
    
    Returns:
        Geparste Argumente
    """
    parser = argparse.ArgumentParser(description="BetterFinder - Schnelle Dateisuche für Windows")
    
    # Argumente für die Kommandozeilennutzung
    parser.add_argument("--search", help="Führt eine Suche durch und gibt die Ergebnisse aus")
    parser.add_argument("--type", help="Filtert die Suche nach Dateityp (z.B. .txt, .pdf)")
    parser.add_argument("--reindex", action="store_true", help="Indiziert das Dateisystem neu")
    
    return parser.parse_args()


def run_command_line(args):
    """
    Führt Kommandozeilenbefehle aus
    
    Args:
        args: Geparste Kommandozeilenargumente
        
    Returns:
        True, wenn die Anwendung im GUI-Modus gestartet werden soll,
        False, wenn sie beendet werden soll
    """
    # Wenn --reindex angegeben wurde
    if args.reindex:
        print("Indizierung wird durchgeführt...")
        # Hier würde eine direkte Indizierung erfolgen
        # In diesem Fall starten wir trotzdem die GUI, die die Indizierung übernimmt
        return True
        
    # Wenn eine Suche durchgeführt werden soll
    if args.search:
        print(f"Suche nach: {args.search}")
        if args.type:
            print(f"Dateityp-Filter: {args.type}")
        # Hier könnte eine direkte Suche implementiert werden
        # Für diese Version starten wir die GUI
        return True
        
    # Standardmäßig GUI starten
    return True


def main():
    """
    Haupteinstiegspunkt
    """
    # Kommandozeilenargumente parsen
    args = parse_arguments()
    
    # Prüfen, ob ein Kommandozeilenbefehl ausgeführt werden soll
    should_start_gui = run_command_line(args)
    
    if should_start_gui:
        # GUI-Modus starten
        app = QApplication(sys.argv)
        app.setApplicationName("BetterFinder")
        app.setOrganizationName("BetterFinder")
        
        # Hauptfenster erstellen (mit Tray-Icon, kein sichtbares Fenster)
        window = MainWindow()
        
        # Anwendung ausführen
        sys.exit(app.exec_())


if __name__ == "__main__":
    main() 