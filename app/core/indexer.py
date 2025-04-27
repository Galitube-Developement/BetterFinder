"""
Dateisystem-Indexierungsmodul für BetterFinder

Dieses Modul ist verantwortlich für:
1. Erstellen eines Index aller Dateien und Ordner
2. Aktualisieren des Index bei Dateisystemänderungen
3. Speichern und Laden des Index
"""

import os
import sqlite3
import time
import threading
import logging
import queue
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
import win32file
import win32con
import win32api
import pywintypes

class FileSystemIndexer:
    """Klasse zur Indexierung des Dateisystems"""
    
    def __init__(self, db_path: str = "index.db"):
        """
        Initialisiert den Indexer
        
        Args:
            db_path: Pfad zur SQLite-Datenbank für den Index
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.running = False
        self.watch_thread = None
        self.index_thread = None
        self.drives = []
        self.file_queue = queue.Queue()
        self.db_lock = threading.Lock()  # Lock für Datenbankzugriff
        self.setup_database()
        
    def setup_database(self):
        """Erstellt die Datenbankverbindung und -tabellen"""
        # Die Datenbankverbindung erfolgt im Hauptthread
        with self.db_lock:
            try:
                # Datenbank mit Timeout öffnen
                self.conn = sqlite3.connect(self.db_path, timeout=20.0)
                
                # Einstellungen für bessere Nebenläufigkeit
                self.conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging für bessere Nebenläufigkeit
                self.conn.execute("PRAGMA synchronous=NORMAL")  # Bessere Performance
                self.conn.execute("PRAGMA busy_timeout=10000")  # 10 Sekunden warten, wenn die DB gesperrt ist
                
                self.cursor = self.conn.cursor()
                
                # Tabelle für Dateien erstellen
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY,
                    filename TEXT,
                    path TEXT,
                    size INTEGER,
                    last_modified INTEGER,
                    file_type TEXT,
                    UNIQUE(path, filename)
                )
                ''')
                
                # Indizes für schnelle Suche erstellen
                self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_filename ON files (filename)')
                self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_path ON files (path)')
                self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_type ON files (file_type)')
                
                self.conn.commit()
            except sqlite3.Error as e:
                print(f"Fehler beim Einrichten der Datenbank: {e}")
                # Fallback auf In-Memory-Datenbank bei Fehler
                self.conn = sqlite3.connect(":memory:")
                self.cursor = self.conn.cursor()
    
    def get_drives(self) -> List[str]:
        """
        Gibt alle verfügbaren Laufwerke zurück
        
        Returns:
            Liste der Laufwerksbuchstaben (z.B. ["C:", "D:"])
        """
        drives = []
        bitmask = win32api.GetLogicalDrives()
        for letter in range(65, 91):  # A-Z
            if bitmask & 1:
                drive = chr(letter) + ":"
                try:
                    drive_type = win32file.GetDriveType(drive)
                    # Nur lokale Festplatten und Netzlaufwerke indizieren
                    if drive_type in (win32con.DRIVE_FIXED, win32con.DRIVE_REMOTE):
                        drives.append(drive)
                except:
                    pass
            bitmask >>= 1
        return drives
    
    def start_indexing(self):
        """Startet den Indizierungsprozess für alle verfügbaren Laufwerke"""
        # Zuerst prüfen, ob bereits ein Indizierungsprozess läuft
        if self.index_thread and self.index_thread.is_alive():
            print("Indizierung läuft bereits, bitte warten...")
            return
            
        self.drives = self.get_drives()
        
        # SQLite-Operationen müssen im selben Thread erfolgen
        self.index_thread = threading.Thread(target=self._indexing_worker)
        self.index_thread.daemon = True
        self.index_thread.start()
        
        # Separate Threads für das Scannen der Laufwerke
        scan_threads = []
        for drive in self.drives:
            thread = threading.Thread(target=self.scan_directory, args=(drive + "\\",))
            thread.daemon = True
            scan_threads.append(thread)
            thread.start()
        
        # Warten auf Abschluss aller Scan-Threads
        for thread in scan_threads:
            thread.join()
            
        # Signal zum Ende des Scannings
        self.file_queue.put(None)
        
        # Nach der Indizierung Überwachung starten
        self.start_watching()
    
    def scan_directory(self, directory: str):
        """
        Scannt ein Verzeichnis rekursiv und fügt Dateien zur Warteschlange hinzu
        
        Args:
            directory: Zu scannendes Verzeichnis
        """
        try:
            for root, dirs, files in os.walk(directory):
                # Dateien zur Warteschlange hinzufügen
                for file in files:
                    try:
                        full_path = os.path.join(root, file)
                        file_stats = os.stat(full_path)
                        size = file_stats.st_size
                        last_modified = int(file_stats.st_mtime)
                        file_type = os.path.splitext(file)[1].lower()
                        
                        # Datei zur Queue hinzufügen
                        self.file_queue.put({
                            'filename': file,
                            'path': root,
                            'size': size,
                            'last_modified': last_modified,
                            'file_type': file_type
                        })
                    except (PermissionError, FileNotFoundError, OSError):
                        # Manche Dateien können nicht zugänglich sein
                        continue
        except (PermissionError, FileNotFoundError, OSError):
            # Manche Verzeichnisse können nicht zugänglich sein
            pass
    
    def _indexing_worker(self):
        """Thread-Methode für die Indexierung der Dateien"""
        # Eigene Datenbankverbindung für diesen Thread erstellen
        try:
            thread_conn = sqlite3.connect(self.db_path, timeout=30.0)
            # Bessere Nebenläufigkeit
            thread_conn.execute("PRAGMA journal_mode=WAL")
            thread_conn.execute("PRAGMA synchronous=NORMAL")
            thread_conn.execute("PRAGMA busy_timeout=15000")
            thread_cursor = thread_conn.cursor()
            
            batch = []
            batch_size = 1000
            
            while True:
                try:
                    file_info = self.file_queue.get(timeout=60.0)  # 60 Sekunden Timeout
                    
                    # None signalisiert das Ende der Warteschlange
                    if file_info is None:
                        break
                    
                    # Sammle Dateien für Batch-Einfügung
                    batch.append((
                        file_info['filename'],
                        file_info['path'],
                        file_info['size'],
                        file_info['last_modified'],
                        file_info['file_type']
                    ))
                    
                    # Führe Batch-Einfügung durch, wenn die Batch-Größe erreicht ist
                    if len(batch) >= batch_size:
                        self._execute_batch_insert(thread_conn, thread_cursor, batch)
                        batch = []
                    
                    self.file_queue.task_done()
                except queue.Empty:
                    # Timeout bei leerer Queue - prüfen, ob noch Dateien zum Einfügen
                    if batch:
                        self._execute_batch_insert(thread_conn, thread_cursor, batch)
                        batch = []
                    else:
                        # Keine Dateien mehr, wir sind fertig
                        break
                except Exception as e:
                    # Fehler beim Verarbeiten ignorieren
                    print(f"Fehler beim Indizieren: {e}")
                    continue
            
            # Restliche Einträge einfügen
            if batch:
                self._execute_batch_insert(thread_conn, thread_cursor, batch)
            
            # Datenbank schließen
            thread_conn.close()
        except sqlite3.Error as e:
            print(f"Schwerwiegender Datenbankfehler beim Indizieren: {e}")
    
    def _execute_batch_insert(self, conn, cursor, batch):
        """
        Führt eine Batch-Einfügung in die Datenbank durch
        
        Args:
            conn: SQLite-Verbindung
            cursor: SQLite-Cursor
            batch: Liste der einzufügenden Datensätze
        """
        max_retries = 5
        retry_delay = 1.0
        
        for retry in range(max_retries):
            try:
                cursor.executemany('''
                INSERT OR REPLACE INTO files 
                (filename, path, size, last_modified, file_type) 
                VALUES (?, ?, ?, ?, ?)
                ''', batch)
                conn.commit()
                return
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and retry < max_retries - 1:
                    print(f"Datenbank ist gesperrt beim Einfügen, versuche erneut in {retry_delay} Sekunden...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Erhöhe den Delay exponentiell
                else:
                    print(f"Fehler beim Batch-Einfügen nach {retry+1} Versuchen: {e}")
                    # Letzter Versuch: einzeln einfügen
                    if retry == max_retries - 1:
                        self._insert_individually(conn, cursor, batch)
    
    def _insert_individually(self, conn, cursor, batch):
        """
        Fügt Datensätze einzeln ein, wenn Batch-Einfügung fehlschlägt
        
        Args:
            conn: SQLite-Verbindung
            cursor: SQLite-Cursor
            batch: Liste der einzufügenden Datensätze
        """
        for record in batch:
            try:
                cursor.execute('''
                INSERT OR REPLACE INTO files 
                (filename, path, size, last_modified, file_type) 
                VALUES (?, ?, ?, ?, ?)
                ''', record)
                conn.commit()
            except sqlite3.Error:
                # Fehler bei einzelnen Datensätzen ignorieren
                pass
    
    def start_watching(self):
        """Startet die Überwachung von Dateisystemänderungen"""
        self.running = True
        self.watch_thread = threading.Thread(target=self._watch_changes)
        self.watch_thread.daemon = True
        self.watch_thread.start()
    
    def _watch_changes(self):
        """Thread-Methode zur Überwachung von Dateisystemänderungen"""
        # Hier würde die Implementierung der Dateisystemüberwachung kommen
        # mit Windows API (ReadDirectoryChangesW)
        pass
    
    def stop(self):
        """Stoppt den Indexer und die Überwachung"""
        self.running = False
        
        if self.watch_thread and self.watch_thread.is_alive():
            self.watch_thread.join(timeout=1.0)
            
        if self.index_thread and self.index_thread.is_alive():
            # Leere die Queue, damit der Thread beenden kann
            try:
                while not self.file_queue.empty():
                    self.file_queue.get_nowait()
                    self.file_queue.task_done()
            except Exception:
                pass
            
            # Abbruchsignal senden
            self.file_queue.put(None)
            self.index_thread.join(timeout=5.0)
        
        # Datenbank schließen
        with self.db_lock:
            if self.conn:
                try:
                    self.conn.commit()
                    self.conn.close()
                except sqlite3.Error:
                    pass
    
    def search(self, query: str, file_type: str = None) -> List[Dict]:
        """
        Durchsucht den Index nach dem angegebenen Query
        
        Args:
            query: Suchanfrage
            file_type: Optional Dateitypfilter (z.B. ".txt")
            
        Returns:
            Liste der gefundenen Dateien mit Metadaten
        """
        with self.db_lock:
            try:
                # Platzhalter hinzufügen für Teilübereinstimmungen
                search_term = f"%{query}%"
                
                if file_type:
                    self.cursor.execute('''
                    SELECT filename, path, size, last_modified, file_type 
                    FROM files 
                    WHERE filename LIKE ? AND file_type = ?
                    LIMIT 1000
                    ''', (search_term, file_type))
                else:
                    self.cursor.execute('''
                    SELECT filename, path, size, last_modified, file_type 
                    FROM files 
                    WHERE filename LIKE ?
                    LIMIT 1000
                    ''', (search_term,))
                
                results = []
                for row in self.cursor.fetchall():
                    results.append({
                        'filename': row[0],
                        'path': row[1],
                        'size': row[2],
                        'last_modified': row[3],
                        'file_type': row[4],
                        'full_path': os.path.join(row[1], row[0])
                    })
                    
                return results
            except sqlite3.Error as e:
                print(f"Fehler bei der Suche: {e}")
                return [] 