import os
from PIL import Image

def create_icon_from_png(png_path, ico_path):
    """
    Erstellt eine .ico-Datei aus einer .png-Datei mit mehreren Auflösungen
    
    Args:
        png_path: Pfad zur PNG-Datei
        ico_path: Pfad, wo die ICO-Datei gespeichert werden soll
    """
    print(f"Erstelle Icon aus {png_path}...")
    
    if not os.path.exists(png_path):
        print(f"Fehler: Die Datei {png_path} existiert nicht.")
        return False
    
    try:
        # Öffne das Bild
        img = Image.open(png_path)
        
        # Erstelle Versionen in verschiedenen Größen für ein vollständiges Icon
        icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        
        # Speichere als ICO mit verschiedenen Größen
        img.save(ico_path, format='ICO', sizes=icon_sizes)
        
        print(f"Icon erfolgreich erstellt: {ico_path}")
        
        # Überprüfe die Dateigröße
        size = os.path.getsize(ico_path)
        print(f"Icon-Dateigröße: {size} Bytes")
        
        return True
    except Exception as e:
        print(f"Fehler beim Erstellen des Icons: {e}")
        return False

if __name__ == "__main__":
    # Pfade für die Dateien
    png_path = os.path.join("app", "resources", "BetterFinder-Icon.png")
    ico_path = os.path.join("app", "resources", "icon.ico")
    
    # Erstelle das Icon
    success = create_icon_from_png(png_path, ico_path)
    
    if success:
        print("Icon wurde erfolgreich erstellt und kann nun für die Anwendung und den Installer verwendet werden.")
    else:
        print("Fehler beim Erstellen des Icons.") 