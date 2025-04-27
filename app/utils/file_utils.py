"""
Hilfsfunktionen für den Umgang mit Dateien

Dieses Modul enthält Hilfsfunktionen für:
1. Formatieren von Dateigrößen
2. Formatieren von Datum und Zeit
3. Öffnen von Dateien
4. Öffnen von Dateiordnern
"""

import os
import subprocess
import platform
from datetime import datetime
from typing import Union, Optional

def get_file_size_str(size_bytes: int) -> str:
    """
    Formatiert eine Dateigröße in Bytes zu einer lesbaren Größe
    
    Args:
        size_bytes: Größe in Bytes
        
    Returns:
        Formatierte Größe als String (z.B. "1,5 MB")
    """
    # Für 0 Byte
    if size_bytes == 0:
        return "0 B"
    
    # Größeneinheiten
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    
    # Einheit bestimmen
    unit_index = 0
    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024
        unit_index += 1
    
    # Formatierung
    if unit_index == 0:
        # Keine Dezimalstellen für Bytes
        return f"{size_bytes:.0f} {units[unit_index]}"
    else:
        # Eine Dezimalstelle für größere Einheiten
        return f"{size_bytes:.1f} {units[unit_index]}".replace(".", ",")

def get_file_date_str(timestamp: Union[int, float]) -> str:
    """
    Formatiert einen Unix-Zeitstempel zu einem lesbaren Datum
    
    Args:
        timestamp: Unix-Zeitstempel
        
    Returns:
        Formatiertes Datum als String (z.B. "25.04.2023 14:30")
    """
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%d.%m.%Y %H:%M")

def open_file(file_path: str) -> bool:
    """
    Öffnet eine Datei mit der Standard-Anwendung
    
    Args:
        file_path: Pfad zur Datei
        
    Returns:
        True bei Erfolg, False bei Fehler
    """
    if not os.path.exists(file_path):
        return False
    
    try:
        if platform.system() == 'Windows':
            os.startfile(file_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.call(['open', file_path])
        else:  # Linux und andere
            subprocess.call(['xdg-open', file_path])
        return True
    except Exception:
        return False

def open_containing_folder(file_path: str) -> bool:
    """
    Öffnet den Ordner, der die angegebene Datei enthält
    
    Args:
        file_path: Pfad zur Datei
        
    Returns:
        True bei Erfolg, False bei Fehler
    """
    if not os.path.exists(file_path):
        return False
    
    try:
        folder_path = os.path.dirname(file_path)
        
        if platform.system() == 'Windows':
            # Ordner im Explorer öffnen und Datei auswählen
            subprocess.call(['explorer', '/select,', file_path])
        elif platform.system() == 'Darwin':  # macOS
            # Ordner im Finder öffnen
            subprocess.call(['open', folder_path])
        else:  # Linux und andere
            # Ordner im Dateimanager öffnen
            subprocess.call(['xdg-open', folder_path])
        return True
    except Exception:
        return False

def is_hidden_file(file_path: str) -> bool:
    """
    Prüft, ob eine Datei versteckt ist
    
    Args:
        file_path: Pfad zur Datei
        
    Returns:
        True, wenn die Datei versteckt ist, sonst False
    """
    if platform.system() == 'Windows':
        import win32api
        import win32con
        
        try:
            attrs = win32api.GetFileAttributes(file_path)
            return bool(attrs & win32con.FILE_ATTRIBUTE_HIDDEN)
        except:
            return False
    else:
        # Unter Unix/Linux sind Dateien mit vorangestelltem Punkt versteckt
        return os.path.basename(file_path).startswith('.')

def get_file_type_icon(file_path: str) -> Optional[str]:
    """
    Gibt den Pfad zu einem passenden Icon für den Dateityp zurück
    
    Args:
        file_path: Pfad zur Datei
        
    Returns:
        Pfad zum Icon oder None, wenn kein passendes Icon gefunden wurde
    """
    # Diese Funktion würde standardmäßig Icons für verschiedene Dateitypen zurückgeben
    # Für dieses Beispiel geben wir None zurück
    return None

def create_directories_for_path(file_path: str) -> bool:
    """
    Erstellt alle erforderlichen Verzeichnisse für einen Dateipfad
    
    Args:
        file_path: Pfad zur Datei
        
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        return True
    except Exception:
        return False 