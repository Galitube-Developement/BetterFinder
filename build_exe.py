import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

def build_exe():
    print("BetterFinder .exe Builder")
    print("========================")
    
    # Prüfe, ob wir im richtigen Verzeichnis sind
    if not os.path.exists("app") or not os.path.exists("app/main.py"):
        print("Fehler: Dieses Skript muss im Hauptverzeichnis des BetterFinder-Projekts ausgeführt werden.")
        return 1
    
    # Versuche, laufende Prozesse zu beenden
    try:
        print("Versuche laufende BetterFinder-Prozesse zu beenden...")
        subprocess.run(["taskkill", "/F", "/IM", "BetterFinder.exe"], shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        # Kurz warten, damit die Prozesse Zeit haben, sich zu beenden
        time.sleep(1)
    except:
        # Ignoriere Fehler, wenn kein Prozess gefunden wurde
        pass
    
    # Bereinige alte Build-Verzeichnisse
    for dir_name in ["build", "dist"]:
        if os.path.exists(dir_name):
            print(f"Entferne vorhandenes {dir_name}-Verzeichnis...")
            try:
                shutil.rmtree(dir_name, ignore_errors=True)
                # Warten, bis Verzeichnisse gelöscht sind
                timeout = 5
                start_time = time.time()
                while os.path.exists(dir_name) and time.time() - start_time < timeout:
                    time.sleep(0.5)
                
                if os.path.exists(dir_name):
                    print(f"Warnung: Konnte {dir_name} nicht vollständig löschen.")
            except Exception as e:
                print(f"Warnung: Fehler beim Löschen von {dir_name}: {e}")
    
    # Entferne auch .spec-Datei
    spec_file = "BetterFinder.spec"
    if os.path.exists(spec_file):
        try:
            os.remove(spec_file)
            print(f"Bestehende {spec_file} entfernt.")
        except Exception as e:
            print(f"Warnung: Konnte {spec_file} nicht löschen: {e}")
    
    # Entferne bestehende .exe im Hauptverzeichnis, falls vorhanden
    exe_path = "BetterFinder.exe"
    if os.path.exists(exe_path):
        try:
            os.remove(exe_path)
            print(f"Bestehende {exe_path} entfernt.")
        except Exception as e:
            print(f"Warnung: Konnte {exe_path} nicht löschen: {e}")
    
    # PyInstaller-Befehl erstellen
    pyinstaller_cmd = [
        "pyinstaller",
        "--name=BetterFinder",
        "--onefile",  # Eine einzelne .exe-Datei erstellen
        "--windowed",  # Keine Konsole anzeigen (für GUI-Anwendungen)
        "--clean",  # Bereinige vor dem Build
        "--noconfirm",  # Bestehende Dateien ohne Nachfrage überschreiben
        "--add-data=app/resources;app/resources",  # Ressourcen einbinden
    ]
    
    # Icon nicht mehr verwenden, da es Probleme verursacht
    # if icon_path:
    #     pyinstaller_cmd.append(f"--icon={icon_path}")
    
    # Hauptdatei hinzufügen
    pyinstaller_cmd.append("app/main.py")
    
    # Befehl ausführen
    print("Starte PyInstaller...")
    print(f"Befehl: {' '.join(pyinstaller_cmd)}")
    
    try:
        process = subprocess.run(pyinstaller_cmd, check=True)
        if process.returncode != 0:
            print(f"Fehler: PyInstaller wurde mit Code {process.returncode} beendet.")
            return 1
    except subprocess.CalledProcessError as e:
        print(f"Fehler: {e}")
        return 1
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")
        return 1
    
    # Überprüfe, ob die .exe erstellt wurde
    dist_exe_path = os.path.join("dist", "BetterFinder.exe")
    if not os.path.exists(dist_exe_path):
        print("Fehler: Die .exe-Datei wurde nicht erstellt.")
        return 1
    
    print("\nBuild erfolgreich abgeschlossen!")
    print(f"Die ausführbare Datei wurde erstellt unter: {os.path.abspath(dist_exe_path)}")
    print("Du kannst diese Datei jetzt auf jedem Windows-Computer verwenden, auch ohne Python-Installation.")
    
    # Optionales Kopieren in das Hauptverzeichnis
    try:
        shutil.copy2(dist_exe_path, "BetterFinder.exe")
        print(f"Eine Kopie wurde auch im aktuellen Verzeichnis erstellt: {os.path.abspath('BetterFinder.exe')}")
    except Exception as e:
        print(f"Warnung: Konnte die .exe nicht ins Hauptverzeichnis kopieren: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(build_exe()) 