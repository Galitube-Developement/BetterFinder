"""
Suchmodul für BetterFinder

Dieses Modul bietet erweiterte Suchfunktionen:
1. Unterstützung für Suchoperatoren (AND, OR, NOT)
2. Platzhaltersuche
3. Reguläre Ausdrücke
4. Parsing komplexer Suchanfragen
"""

import re
import os
import sqlite3
import threading
import time
from typing import List, Dict, Optional, Set, Union, Tuple

class SearchEngine:
    """Erweiterte Suchmaschine für BetterFinder"""
    
    def __init__(self, db_path: str = "index.db"):
        """
        Initialisiert die Suchmaschine
        
        Args:
            db_path: Pfad zur SQLite-Datenbank mit dem Index
        """
        self.db_path = db_path
        self.local = threading.local()  # Thread-lokale Speicherung für Datenbankverbindungen
        self.connection_lock = threading.Lock()  # Lock für Datenbankverbindungen
    
    def _get_connection(self):
        """
        Gibt eine thread-lokale Datenbankverbindung zurück
        
        Returns:
            SQLite-Verbindung und Cursor als Tuple
        """
        # Prüfen, ob der aktuelle Thread bereits eine Verbindung hat
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            # Neue Verbindung für diesen Thread erstellen
            with self.connection_lock:
                try:
                    self.local.conn = sqlite3.connect(self.db_path, timeout=10.0)  # 10 Sekunden Timeout
                    self.local.conn.row_factory = sqlite3.Row
                    # Pragmas für bessere Nebenläufigkeit
                    self.local.conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
                    self.local.conn.execute("PRAGMA busy_timeout=5000")  # 5 Sekunden bei Blockierung warten
                    self.local.cursor = self.local.conn.cursor()
                except sqlite3.Error as e:
                    print(f"Fehler beim Verbinden zur Datenbank: {e}")
                    # Fallback auf eine In-Memory-Datenbank, wenn die echte Datenbank nicht zugänglich ist
                    self.local.conn = sqlite3.connect(":memory:")
                    self.local.conn.row_factory = sqlite3.Row
                    self.local.cursor = self.local.conn.cursor()
        
        return self.local.conn, self.local.cursor
    
    def close(self):
        """Datenbankverbindung schließen"""
        if hasattr(self.local, 'conn') and self.local.conn:
            try:
                self.local.conn.close()
            except sqlite3.Error:
                pass  # Ignoriere Fehler beim Schließen
            self.local.conn = None
            self.local.cursor = None
    
    def search(self, query: str, file_type: Optional[str] = None, 
               max_results: int = 1000) -> List[Dict]:
        """
        Führt eine Suche mit dem angegebenen Query durch
        
        Args:
            query: Suchanfrage (kann Operatoren enthalten)
            file_type: Optionaler Dateitypfilter
            max_results: Maximale Anzahl an Ergebnissen
            
        Returns:
            Liste der gefundenen Dateien
        """
        try:
            # Prüfen, ob es sich um eine einfache oder komplexe Suche handelt
            if any(op in query for op in ['AND', 'OR', 'NOT']) or '*' in query or '?' in query:
                return self._complex_search(query, file_type, max_results)
            else:
                return self._simple_search(query, file_type, max_results)
        except sqlite3.Error as e:
            print(f"Datenbankfehler bei der Suche: {e}")
            return []  # Leere Liste zurückgeben bei Fehler
    
    def _simple_search(self, query: str, file_type: Optional[str], max_results: int) -> List[Dict]:
        """
        Einfache Suche ohne Operatoren
        
        Args:
            query: Einfache Suchanfrage
            file_type: Optionaler Dateitypfilter
            max_results: Maximale Anzahl an Ergebnissen
            
        Returns:
            Liste der gefundenen Dateien
        """
        # Thread-lokale Verbindung verwenden
        conn, cursor = self._get_connection()
        
        # Platzhalter für Teilübereinstimmungen
        search_term = f"%{query}%"
        
        sql = '''
        SELECT filename, path, size, last_modified, file_type 
        FROM files 
        WHERE filename LIKE ?
        '''
        params = [search_term]
        
        if file_type:
            sql += " AND file_type = ?"
            params.append(file_type)
        
        sql += f" LIMIT {max_results}"
        
        # Mit Retry-Logik für gesperrte Datenbank
        max_retries = 3
        retry_delay = 1.0  # Sekunden
        
        for retry in range(max_retries):
            try:
                cursor.execute(sql, params)
                break  # Erfolgreiche Ausführung
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and retry < max_retries - 1:
                    print(f"Datenbank ist gesperrt, versuche erneut in {retry_delay} Sekunden...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponentiell erhöhen
                    # Neue Verbindung versuchen
                    self.close()
                    conn, cursor = self._get_connection()
                else:
                    raise  # Andere Fehler oder zu viele Versuche
        
        results = []
        try:
            for row in cursor:
                results.append({
                    'filename': row['filename'],
                    'path': row['path'],
                    'size': row['size'],
                    'last_modified': row['last_modified'],
                    'file_type': row['file_type'],
                    'full_path': os.path.join(row['path'], row['filename'])
                })
        except Exception as e:
            print(f"Fehler beim Verarbeiten der Suchergebnisse: {e}")
            
        return results
    
    def _complex_search(self, query: str, file_type: Optional[str], max_results: int) -> List[Dict]:
        """
        Komplexe Suche mit Operatoren
        
        Args:
            query: Komplexe Suchanfrage mit Operatoren
            file_type: Optionaler Dateitypfilter
            max_results: Maximale Anzahl an Ergebnissen
            
        Returns:
            Liste der gefundenen Dateien
        """
        # Thread-lokale Verbindung verwenden
        conn, cursor = self._get_connection()
        
        # Parse die Abfrage
        parsed_query = self._parse_query(query)
        
        # Erstelle die SQL-Abfrage basierend auf der geparsten Anfrage
        sql, params = self._build_sql_from_parsed_query(parsed_query, file_type, max_results)
        
        # Mit Retry-Logik für gesperrte Datenbank
        max_retries = 3
        retry_delay = 1.0  # Sekunden
        
        for retry in range(max_retries):
            try:
                cursor.execute(sql, params)
                break  # Erfolgreiche Ausführung
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and retry < max_retries - 1:
                    print(f"Datenbank ist gesperrt, versuche erneut in {retry_delay} Sekunden...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponentiell erhöhen
                    # Neue Verbindung versuchen
                    self.close()
                    conn, cursor = self._get_connection()
                else:
                    raise  # Andere Fehler oder zu viele Versuche
        
        results = []
        try:
            for row in cursor:
                results.append({
                    'filename': row['filename'],
                    'path': row['path'],
                    'size': row['size'],
                    'last_modified': row['last_modified'],
                    'file_type': row['file_type'],
                    'full_path': os.path.join(row['path'], row['filename'])
                })
        except Exception as e:
            print(f"Fehler beim Verarbeiten der Suchergebnisse: {e}")
            
        return results
    
    def _parse_query(self, query: str) -> Dict:
        """
        Parst eine komplexe Suchanfrage
        
        Args:
            query: Komplexe Suchanfrage
            
        Returns:
            Geparste Anfrage als Dictionary
        """
        # Einfacher Parser für die Demo - eine vollständige Implementierung
        # würde einen richtigen Abfrageparser verwenden
        parsed = {
            'type': 'simple',
            'value': query
        }
        
        # Erkennen von AND-Operationen
        if ' AND ' in query:
            parts = query.split(' AND ')
            parsed = {
                'type': 'and',
                'operands': [{'type': 'simple', 'value': part.strip()} for part in parts]
            }
        
        # Erkennen von OR-Operationen
        elif ' OR ' in query:
            parts = query.split(' OR ')
            parsed = {
                'type': 'or',
                'operands': [{'type': 'simple', 'value': part.strip()} for part in parts]
            }
        
        # Erkennen von NOT-Operationen
        elif query.startswith('NOT '):
            parsed = {
                'type': 'not',
                'operand': {'type': 'simple', 'value': query[4:].strip()}
            }
        
        # Platzhalter in reguläre Ausdrücke umwandeln
        if '*' in query or '?' in query:
            if parsed['type'] == 'simple':
                # Umwandeln von Datei-Platzhaltern in SQL-LIKE-Platzhalter
                value = parsed['value']
                value = value.replace('*', '%').replace('?', '_')
                parsed['value'] = value
        
        return parsed
    
    def _build_sql_from_parsed_query(self, parsed_query: Dict, file_type: Optional[str], 
                                     max_results: int) -> Tuple[str, List]:
        """
        Erstellt eine SQL-Abfrage aus einer geparsten Anfrage
        
        Args:
            parsed_query: Geparste Anfrage
            file_type: Optionaler Dateitypfilter
            max_results: Maximale Anzahl an Ergebnissen
            
        Returns:
            SQL-Abfrage und Parameter als Tuple
        """
        base_sql = '''
        SELECT filename, path, size, last_modified, file_type 
        FROM files 
        WHERE 
        '''
        
        where_clause, params = self._build_where_clause(parsed_query)
        
        sql = base_sql + where_clause
        
        if file_type:
            sql += " AND file_type = ?"
            params.append(file_type)
        
        sql += f" LIMIT {max_results}"
        
        return sql, params
    
    def _build_where_clause(self, parsed_query: Dict) -> Tuple[str, List]:
        """
        Erstellt die WHERE-Klausel für eine SQL-Abfrage
        
        Args:
            parsed_query: Geparste Anfrage
            
        Returns:
            WHERE-Klausel und Parameter als Tuple
        """
        query_type = parsed_query['type']
        
        if query_type == 'simple':
            value = parsed_query['value']
            if '%' in value or '_' in value:
                # Für Platzhaltersuche
                return "filename LIKE ?", [value]
            else:
                # Für normale Suche
                return "filename LIKE ?", [f"%{value}%"]
        
        elif query_type == 'and':
            clauses = []
            params = []
            
            for operand in parsed_query['operands']:
                clause, clause_params = self._build_where_clause(operand)
                clauses.append(clause)
                params.extend(clause_params)
            
            return "(" + " AND ".join(clauses) + ")", params
        
        elif query_type == 'or':
            clauses = []
            params = []
            
            for operand in parsed_query['operands']:
                clause, clause_params = self._build_where_clause(operand)
                clauses.append(clause)
                params.extend(clause_params)
            
            return "(" + " OR ".join(clauses) + ")", params
        
        elif query_type == 'not':
            clause, clause_params = self._build_where_clause(parsed_query['operand'])
            return f"NOT ({clause})", clause_params
        
        return "", []
    
    def search_by_regex(self, regex_pattern: str, file_type: Optional[str] = None, 
                        max_results: int = 1000) -> List[Dict]:
        """
        Sucht nach Dateien mit einem regulären Ausdruck
        
        Args:
            regex_pattern: Regulärer Ausdruck
            file_type: Optionaler Dateitypfilter
            max_results: Maximale Anzahl an Ergebnissen
            
        Returns:
            Liste der gefundenen Dateien
        """
        # Thread-lokale Verbindung verwenden
        conn, cursor = self._get_connection()
        
        # SQLite unterstützt keine regulären Ausdrücke nativ,
        # daher werden alle Dateien geholt und dann gefiltert
        
        sql = "SELECT filename, path, size, last_modified, file_type FROM files"
        params = []
        
        if file_type:
            sql += " WHERE file_type = ?"
            params.append(file_type)
        
        sql += f" LIMIT {max_results * 10}"  # Mehr holen, da wir filtern werden
        
        # Mit Retry-Logik für gesperrte Datenbank
        max_retries = 3
        retry_delay = 1.0  # Sekunden
        
        for retry in range(max_retries):
            try:
                cursor.execute(sql, params)
                break  # Erfolgreiche Ausführung
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and retry < max_retries - 1:
                    print(f"Datenbank ist gesperrt, versuche erneut in {retry_delay} Sekunden...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponentiell erhöhen
                    # Neue Verbindung versuchen
                    self.close()
                    conn, cursor = self._get_connection()
                else:
                    raise  # Andere Fehler oder zu viele Versuche
        
        results = []
        pattern = re.compile(regex_pattern, re.IGNORECASE)
        
        try:
            for row in cursor:
                if pattern.search(row['filename']):
                    results.append({
                        'filename': row['filename'],
                        'path': row['path'],
                        'size': row['size'],
                        'last_modified': row['last_modified'],
                        'file_type': row['file_type'],
                        'full_path': os.path.join(row['path'], row['filename'])
                    })
                    
                    if len(results) >= max_results:
                        break
        except Exception as e:
            print(f"Fehler beim Verarbeiten der Regex-Ergebnisse: {e}")
        
        return results 