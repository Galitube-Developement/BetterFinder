"""
Hauptfenster der Anwendung

Dieses Modul definiert das Hauptfenster der Anwendung mit:
1. Spotlight-ähnliche Suchoberfläche
2. Tray-Icon mit Einstellungen und Neuindizierung
"""

import os
import sys
import time
import webbrowser
import traceback
from datetime import datetime
from typing import List, Dict, Optional

from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QLabel,
    QComboBox, QStatusBar, QMenu, QAction, QFileDialog, QMessageBox,
    QHeaderView, QSystemTrayIcon, QSplitter, QTabWidget, QCheckBox,
    QToolBar, QShortcut, QFrame, QGridLayout, QListWidget, QListWidgetItem,
    QGraphicsDropShadowEffect, QDialog, QDesktopWidget, QGroupBox, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings, QSize, QRect, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence, QFont, QColor, QPalette, QFontMetrics, QRegion, QPainterPath

from app.core.indexer import FileSystemIndexer
from app.core.search_engine import SearchEngine
from app.utils.file_utils import get_file_size_str, get_file_date_str, open_file, open_containing_folder

# Konstantendefinitionen für das Styling
BACKGROUND_COLOR = "#202020"
TEXT_COLOR = "#FFFFFF"
HIGHLIGHT_COLOR = "#0078D7"
SECONDARY_COLOR = "#303030"
BORDER_COLOR = "#404040"
ICON_COLOR = "#808080"

# Kommando-Präfixe
COMMANDS = {
    "=": "Berechnet mathematische Ausdrücke",
    "!": "Greift auf vorherige Ergebnisse zu",
    "?": "Sucht Dateien und Ordner",
    "@": "Öffnet Einstellungen und Optionen",
    ".": "Sucht Programme"
}

class SearchThread(QThread):
    """Thread für die Suche, um die UI nicht zu blockieren"""
    
    # Signal, das die Suchergebnisse zurückgibt
    results_ready = pyqtSignal(list)
    # Signal für Fehler
    error_occurred = pyqtSignal(str)
    
    def __init__(self, search_engine: SearchEngine, query: str, file_type: Optional[str] = None):
        """
        Initialisiert den Suchthread
        
        Args:
            search_engine: Die Suchmaschine
            query: Die Suchanfrage
            file_type: Optionaler Dateitypfilter
        """
        super().__init__()
        self.search_engine = search_engine
        self.query = query
        self.file_type = file_type
        self.stop_requested = False
    
    def run(self):
        """Führt die Suche durch"""
        try:
            # Frühzeitige Prüfung auf Abbruch
            if self.stop_requested:
                return
                
            # Prüfen, ob es ein regulärer Ausdruck ist
            if self.query.startswith('regex:'):
                regex_pattern = self.query[6:].strip()
                results = self.search_engine.search_by_regex(regex_pattern, self.file_type)
            # Prüfen auf Kommandopräfixe
            elif self.query.startswith('='):
                # Mathematischer Ausdruck
                try:
                    expression = self.query[1:].strip()
                    result = eval(expression, {"__builtins__": {}}, {})
                    results = [{"filename": f"{expression} = {result}", "path": "Berechnung", 
                              "size": 0, "last_modified": datetime.now(), "full_path": str(result),
                              "type": "calculation"}]
                except:
                    results = []
            elif self.query.startswith('@'):
                # Einstellungen anzeigen
                cmd = self.query[1:].strip().lower()
                results = [{"filename": "Einstellungen öffnen", "path": "BetterFinder", 
                          "size": 0, "last_modified": datetime.now(), "full_path": "settings",
                          "type": "command"}]
            else:
                results = self.search_engine.search(self.query, self.file_type)
            
            # Ergebnisse zurücksenden, falls kein Abbruch angefordert wurde
            if not self.stop_requested:
                self.results_ready.emit(results)
        except Exception as e:
            # Bei Fehler Signal senden, falls kein Abbruch angefordert wurde
            if not self.stop_requested:
                error_msg = f"Fehler bei der Suche: {str(e)}"
                self.error_occurred.emit(error_msg)
                # Leere Ergebnisliste zurückgeben
                self.results_ready.emit([])
            # Vollständige Fehlerinfo im Terminal ausgeben
            print(f"Suchfehler: {e}")
            traceback.print_exc()
    
    def stop(self):
        """Fordert den Abbruch des Threads an"""
        self.stop_requested = True

class IndexingThread(QThread):
    """Thread für die Indizierung des Dateisystems"""
    
    # Signal für Fortschritt
    progress = pyqtSignal(str)
    # Signal für Fertigstellung
    finished_indexing = pyqtSignal()
    # Signal für Fehler
    error_occurred = pyqtSignal(str)
    
    def __init__(self, indexer: FileSystemIndexer):
        """
        Initialisiert den Indizierungsthread
        
        Args:
            indexer: Der Dateisystem-Indexer
        """
        super().__init__()
        self.indexer = indexer
    
    def run(self):
        """Führt die Indizierung durch"""
        try:
            self.progress.emit("Indizierung gestartet...")
            self.indexer.start_indexing()
            self.progress.emit("Indizierung abgeschlossen.")
            self.finished_indexing.emit()
        except Exception as e:
            # Bei Fehler Signal senden
            error_msg = f"Fehler bei der Indizierung: {str(e)}"
            self.error_occurred.emit(error_msg)
            self.progress.emit("Indizierung fehlgeschlagen.")
            # Vollständige Fehlerinfo im Terminal ausgeben
            print(f"Indizierungsfehler: {e}")
            traceback.print_exc()

class SpotlightStyleSearchBar(QWidget):
    """Spotlight-ähnliche Suchleiste"""
    
    search_triggered = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Suchfeld-Container für Radius-Effekt
        search_container = QWidget()
        search_container.setObjectName("searchContainer")
        search_container.setStyleSheet(f"""
            #searchContainer {{
                background-color: {SECONDARY_COLOR};
                border-radius: 25px;
                border: 1px solid {BORDER_COLOR};
                padding: 0px;
            }}
        """)
        
        # Layout für den Container
        container_layout = QHBoxLayout(search_container)
        container_layout.setContentsMargins(15, 0, 15, 0)
        
        # Suchfeld
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Suchen...")
        self.search_box.setMinimumHeight(50)
        
        # Transparentes Suchfeld innerhalb des Containers
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                color: {TEXT_COLOR};
                border: none;
                font-size: 16px;
                padding: 4px;
            }}
        """)
        
        # Hinzufügen zum Container-Layout
        container_layout.addWidget(self.search_box)
        
        # Container zum Hauptlayout hinzufügen
        layout.addWidget(search_container)
        
        # Signale
        self.search_box.returnPressed.connect(self.emit_search)
        self.search_box.textChanged.connect(self.on_text_changed)
        
        # Layout setzen
        self.setLayout(layout)
    
    def on_text_changed(self, text):
        self.search_triggered.emit(text)
    
    def emit_search(self):
        self.search_triggered.emit(self.search_box.text().strip())
        
    def get_text(self):
        return self.search_box.text().strip()
        
    def set_focus(self):
        self.search_box.setFocus()
        self.search_box.selectAll()

class SpotlightResultsList(QListWidget):
    """Liste der Suchergebnisse im Spotlight-Stil"""
    
    item_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Styling
        self.setFrameShape(QFrame.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container für die Ergebnisliste
        self.setObjectName("resultsList")
        
        self.setStyleSheet(f"""
            #resultsList {{
                background-color: {SECONDARY_COLOR};
                color: {TEXT_COLOR};
                border: none;
                border-radius: 25px;
                padding: 15px;
            }}
            QListWidget::item {{
                border-radius: 15px;
                padding: 12px;
                margin-bottom: 5px;
            }}
            QListWidget::item:selected {{
                background-color: {HIGHLIGHT_COLOR};
            }}
            QListWidget::item:hover {{
                background-color: #404040;
            }}
            QScrollBar:vertical {{
                border: none;
                background: {BACKGROUND_COLOR};
                width: 8px;
                margin: 15px 3px 15px 3px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER_COLOR};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        
        # Signale
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
        
    def on_item_double_clicked(self, item):
        data = item.data(Qt.UserRole)
        if data:
            self.item_selected.emit(data)

class SpotlightWindow(QDialog):
    """Hauptfenster im Spotlight-Stil"""
    
    def __init__(self, indexer, search_engine):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        self.indexer = indexer
        self.search_engine = search_engine
        
        # Such-Thread
        self.search_thread = None
        
        # Timer für verzögerte Suche
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        # Schatten-Effekte abschalten für echte Transparenz
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.init_ui()
        
    def init_ui(self):
        # Position und Größe
        screen_geometry = QDesktopWidget().availableGeometry()
        width = min(600, screen_geometry.width() - 100)
        height = 500
        
        x = (screen_geometry.width() - width) // 2
        y = screen_geometry.height() // 4
        
        self.setGeometry(x, y, width, height)
        
        # Der Inhalt des Fensters
        self.content_widget = QWidget(self)
        self.content_widget.setObjectName("contentWidget")
        
        # Extrem runde Ecken für den Inhalt
        self.content_widget.setStyleSheet(f"""
            #contentWidget {{
                background-color: {BACKGROUND_COLOR};
                border-radius: 35px;
                border: 1px solid {BORDER_COLOR};
            }}
        """)
        
        # Layout für das gesamte Fenster (transparenter Hintergrund)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)  # Platz für Schatten
        main_layout.addWidget(self.content_widget)
        
        # Layout für den Inhalt
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)
        
        # Schatten-Effekt für den Inhalt
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.content_widget.setGraphicsEffect(shadow)
        
        # Suchleiste
        self.search_bar = SpotlightStyleSearchBar()
        self.search_bar.search_triggered.connect(self.on_search_triggered)
        content_layout.addWidget(self.search_bar)
        
        # Ergebnisliste
        self.results_list = SpotlightResultsList()
        self.results_list.item_selected.connect(self.on_item_selected)
        content_layout.addWidget(self.results_list)
        
        # Fokus auf Suchfeld
        self.search_bar.set_focus()
    
    def keyPressEvent(self, event):
        # Escape schließt das Fenster
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)
            
    def mousePressEvent(self, event):
        # Fenster kann verschoben werden
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        # Fenster verschieben
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def on_search_triggered(self, text):
        # Verzögerte Suche starten
        self.search_timer.start(300)
        
    def stop_current_search(self):
        """Stoppt den aktuellen Suchthread, falls vorhanden"""
        if self.search_thread and self.search_thread.isRunning():
            if hasattr(self.search_thread, 'stop'):
                self.search_thread.stop()
            
            self.search_thread.disconnect()
            self.search_thread.terminate()
            self.search_thread.wait(500)
            self.search_thread = None
    
    def perform_search(self):
        """Führt die eigentliche Suche durch"""
        query = self.search_bar.get_text()
        
        # Prüfen, ob Suchtext leer ist
        if not query:
            self.results_list.clear()
            return
        
        # Laufenden Thread stoppen
        self.stop_current_search()
        
        # Neuen Suchthread starten
        self.search_thread = SearchThread(self.search_engine, query, None)
        self.search_thread.results_ready.connect(self.display_results)
        self.search_thread.error_occurred.connect(self.show_error)
        self.search_thread.start()
    
    def display_results(self, results):
        """Zeigt die Suchergebnisse an"""
        self.results_list.clear()
        
        for result in results:
            item = QListWidgetItem()
            
            # Item-Text und Icon je nach Typ
            if 'type' in result and result['type'] == 'calculation':
                item.setText(result['filename'])
                # Mathe-Symbol für Berechnungen
                # (hier müsste ein echtes Icon gesetzt werden)
            elif 'type' in result and result['type'] == 'command':
                item.setText(result['filename'])
                # Einstellungs-Symbol für Kommandos
                # (hier müsste ein echtes Icon gesetzt werden)
            else:
                # Normale Datei
                item.setText(f"{result['filename']} - {result['path']}")
                # Dateityp-abhängiges Icon
                # (hier müsste ein echtes Icon gesetzt werden)
            
            # Daten für Doppelklick speichern
            item.setData(Qt.UserRole, result['full_path'])
            
            self.results_list.addItem(item)
    
    def on_item_selected(self, path):
        """Behandelt die Auswahl eines Ergebnisses"""
        if path == 'settings':
            # Einstellungen öffnen
            self.hide()
            return
            
        try:
            # Datei öffnen
            open_file(path)
            self.hide()
        except Exception as e:
            self.show_error(f"Fehler beim Öffnen der Datei: {str(e)}")
    
    def show_error(self, error_message):
        """Zeigt eine Fehlermeldung an"""
        print(f"Fehler: {error_message}")
        # Hier könnte ein Fehler-Icon in der Ergebnisliste angezeigt werden

class SettingsDialog(QDialog):
    """Einstellungsdialog für BetterFinder"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("BetterFinder", "BetterFinder")
        self.setWindowTitle("BetterFinder Einstellungen")
        self.resize(500, 400)
        
        # Transparenter Hintergrund für Rundungen
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Erstelle UI
        self.init_ui()
        
        # Lade bestehende Einstellungen
        self.load_settings()
    
    def init_ui(self):
        # Hauptlayout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Container für den Inhalt
        self.content_widget = QWidget(self)
        self.content_widget.setObjectName("settingsContent")
        self.content_widget.setStyleSheet(f"""
            #settingsContent {{
                background-color: {BACKGROUND_COLOR};
                border-radius: 25px;
                border: 1px solid {BORDER_COLOR};
            }}
        """)
        
        # Inhaltslayout
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(15)
        
        # Titel
        title_label = QLabel("BetterFinder Einstellungen")
        title_label.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 18px; font-weight: bold;")
        content_layout.addWidget(title_label)
        
        # Trennlinie
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"background-color: {BORDER_COLOR};")
        content_layout.addWidget(separator)
        
        # Scroll-Bereich für alle Einstellungen
        scroll_area = QWidget()
        scroll_layout = QVBoxLayout(scroll_area)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(15)
        
        # 1. Hotkey-Einstellung
        hotkey_group = QGroupBox("Tastenkombination")
        hotkey_group.setStyleSheet(f"""
            QGroupBox {{
                color: {TEXT_COLOR};
                font-weight: bold;
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        hotkey_layout = QVBoxLayout(hotkey_group)
        hotkey_description = QLabel("Tastenkombination zum Öffnen von BetterFinder:")
        hotkey_description.setStyleSheet(f"color: {TEXT_COLOR};")
        
        self.hotkey_edit = QLineEdit()
        self.hotkey_edit.setReadOnly(True)
        self.hotkey_edit.setText("Strg+Leertaste")
        self.hotkey_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {SECONDARY_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
        """)
        
        self.hotkey_button = QPushButton("Ändern")
        self.hotkey_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {HIGHLIGHT_COLOR};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #0069c0;
            }}
        """)
        self.hotkey_button.clicked.connect(self.change_hotkey)
        
        hotkey_layout.addWidget(hotkey_description)
        hotkey_layout.addWidget(self.hotkey_edit)
        hotkey_layout.addWidget(self.hotkey_button)
        
        # 2. Autostart-Option
        autostart_group = QGroupBox("Systemstart")
        autostart_group.setStyleSheet(f"""
            QGroupBox {{
                color: {TEXT_COLOR};
                font-weight: bold;
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        autostart_layout = QVBoxLayout(autostart_group)
        self.autostart_checkbox = QCheckBox("BetterFinder beim Systemstart automatisch starten")
        self.autostart_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {TEXT_COLOR};
                spacing: 5px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 2px;
                border: 1px solid {BORDER_COLOR};
            }}
            QCheckBox::indicator:checked {{
                background-color: {HIGHLIGHT_COLOR};
                border: 1px solid {HIGHLIGHT_COLOR};
            }}
        """)
        
        autostart_layout.addWidget(self.autostart_checkbox)
        
        # 3. Ausgeschlossene Verzeichnisse
        exclude_group = QGroupBox("Ausgeschlossene Verzeichnisse")
        exclude_group.setStyleSheet(f"""
            QGroupBox {{
                color: {TEXT_COLOR};
                font-weight: bold;
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        exclude_layout = QVBoxLayout(exclude_group)
        exclude_description = QLabel("Diese Verzeichnisse werden nicht indiziert:")
        exclude_description.setStyleSheet(f"color: {TEXT_COLOR};")
        
        self.exclude_list = QListWidget()
        self.exclude_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {SECONDARY_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 5px;
                border-radius: 3px;
            }}
            QListWidget::item:selected {{
                background-color: {HIGHLIGHT_COLOR};
            }}
        """)
        self.exclude_list.setMaximumHeight(100)
        
        exclude_buttons_layout = QHBoxLayout()
        self.add_exclude_button = QPushButton("Hinzufügen")
        self.add_exclude_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {HIGHLIGHT_COLOR};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #0069c0;
            }}
        """)
        self.add_exclude_button.clicked.connect(self.add_exclude_path)
        
        self.remove_exclude_button = QPushButton("Entfernen")
        self.remove_exclude_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #b71c1c;
            }}
        """)
        self.remove_exclude_button.clicked.connect(self.remove_exclude_path)
        
        exclude_buttons_layout.addWidget(self.add_exclude_button)
        exclude_buttons_layout.addWidget(self.remove_exclude_button)
        
        exclude_layout.addWidget(exclude_description)
        exclude_layout.addWidget(self.exclude_list)
        exclude_layout.addLayout(exclude_buttons_layout)
        
        # 4. Maximale Anzahl der Ergebnisse
        results_group = QGroupBox("Ergebnisse")
        results_group.setStyleSheet(f"""
            QGroupBox {{
                color: {TEXT_COLOR};
                font-weight: bold;
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        results_layout = QVBoxLayout(results_group)
        results_description = QLabel("Maximale Anzahl der angezeigten Suchergebnisse:")
        results_description.setStyleSheet(f"color: {TEXT_COLOR};")
        
        self.results_spinbox = QSpinBox()
        self.results_spinbox.setStyleSheet(f"""
            QSpinBox {{
                background-color: {SECONDARY_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {BORDER_COLOR};
                border-radius: 2px;
            }}
        """)
        self.results_spinbox.setMinimum(10)
        self.results_spinbox.setMaximum(100)
        self.results_spinbox.setSingleStep(5)
        self.results_spinbox.setValue(30)
        
        results_layout.addWidget(results_description)
        results_layout.addWidget(self.results_spinbox)
        
        # Füge alle Gruppen zum Scroll-Layout hinzu
        scroll_layout.addWidget(hotkey_group)
        scroll_layout.addWidget(autostart_group)
        scroll_layout.addWidget(exclude_group)
        scroll_layout.addWidget(results_group)
        scroll_layout.addStretch(1)
        
        # Füge das Scroll-Widget zum Content-Layout hinzu
        content_layout.addWidget(scroll_area)
        
        # Buttons unten
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {SECONDARY_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #404040;
            }}
        """)
        self.cancel_button.clicked.connect(self.reject)
        
        self.save_button = QPushButton("Speichern")
        self.save_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {HIGHLIGHT_COLOR};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #0069c0;
            }}
        """)
        self.save_button.clicked.connect(self.save_settings)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        content_layout.addLayout(button_layout)
        
        # Schatten-Effekt
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.content_widget.setGraphicsEffect(shadow)
        
        # Füge den Content zum Hauptlayout hinzu
        main_layout.addWidget(self.content_widget)
    
    def load_settings(self):
        """Lade bestehende Einstellungen"""
        # Hotkey
        hotkey = self.settings.value("hotkey", "Strg+Leertaste")
        self.hotkey_edit.setText(hotkey)
        
        # Autostart
        autostart = self.settings.value("autostart", False, type=bool)
        self.autostart_checkbox.setChecked(autostart)
        
        # Ausgeschlossene Verzeichnisse
        excluded_paths = self.settings.value("excluded_paths", [], type=list)
        for path in excluded_paths:
            self.exclude_list.addItem(path)
        
        # Maximale Anzahl der Ergebnisse
        max_results = self.settings.value("max_results", 30, type=int)
        self.results_spinbox.setValue(max_results)
    
    def save_settings(self):
        """Speichere die Einstellungen"""
        try:
            # Hotkey
            self.settings.setValue("hotkey", self.hotkey_edit.text())
            
            # Autostart
            self.settings.setValue("autostart", self.autostart_checkbox.isChecked())
            try:
                if self.autostart_checkbox.isChecked():
                    self.setup_autostart(True)
                else:
                    self.setup_autostart(False)
            except Exception as e:
                print(f"Fehler beim Konfigurieren des Autostarts: {e}")
                # Zeige eine Warnung, breche aber nicht ab
                QMessageBox.warning(self, "Autostart-Warnung",
                                  f"Die Autostart-Einstellung konnte nicht angewendet werden: {e}\n\nAlle anderen Einstellungen wurden gespeichert.")
            
            # Ausgeschlossene Verzeichnisse
            excluded_paths = []
            for i in range(self.exclude_list.count()):
                excluded_paths.append(self.exclude_list.item(i).text())
            self.settings.setValue("excluded_paths", excluded_paths)
            
            # Maximale Anzahl der Ergebnisse
            self.settings.setValue("max_results", self.results_spinbox.value())
            
            # Einstellungen speichern
            self.settings.sync()
            
            # Dialog schließen
            self.accept()
        except Exception as e:
            # Zeige Fehlermeldung und breche nicht ab
            print(f"Fehler beim Speichern der Einstellungen: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Fehler", 
                              f"Die Einstellungen konnten nicht gespeichert werden: {str(e)}")
            # Dialog bleibt offen, damit der Benutzer erneut versuchen kann
    
    def change_hotkey(self):
        """Ändere die Tastenkombination"""
        # In einer richtigen Implementierung würde hier ein Dialog angezeigt werden,
        # der einen Tastendruck abfängt und als neue Tastenkombination speichert
        self.hotkey_edit.setText("Strg+Leertaste")  # Platzhalter, würde in Realität durch den erfassten Hotkey ersetzt
    
    def add_exclude_path(self):
        """Füge einen auszuschließenden Pfad hinzu"""
        directory = QFileDialog.getExistingDirectory(self, "Verzeichnis auswählen")
        if directory:
            # Prüfe, ob der Pfad bereits in der Liste ist
            for i in range(self.exclude_list.count()):
                if self.exclude_list.item(i).text() == directory:
                    return
            
            # Füge den Pfad zur Liste hinzu
            self.exclude_list.addItem(directory)
    
    def remove_exclude_path(self):
        """Entferne einen ausgewählten Pfad"""
        selected_items = self.exclude_list.selectedItems()
        for item in selected_items:
            self.exclude_list.takeItem(self.exclude_list.row(item))
    
    def setup_autostart(self, enable):
        """Konfiguriere den Autostart"""
        import os
        import sys
        import ctypes
        
        try:
            # Pfad zur aktuellen ausführbaren Datei
            if getattr(sys, 'frozen', False):
                # Wenn die Anwendung mit PyInstaller erstellt wurde
                app_path = sys.executable
            else:
                # Wenn die Anwendung über Python ausgeführt wird
                app_path = os.path.abspath(sys.argv[0])
            
            # Autostart-Verzeichnis
            startup_dir = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            shortcut_path = os.path.join(startup_dir, 'BetterFinder.lnk')
            bat_path = os.path.join(startup_dir, 'BetterFinder.bat')
            
            # Prüfen, ob das Verzeichnis existiert und schreibbar ist
            if not os.path.exists(startup_dir):
                os.makedirs(startup_dir, exist_ok=True)
                print(f"Autostart-Verzeichnis wurde erstellt: {startup_dir}")
            
            # Prüfen, ob das Verzeichnis schreibbar ist
            if not os.access(startup_dir, os.W_OK):
                raise Exception(f"Keine Schreibrechte für das Autostart-Verzeichnis: {startup_dir}")
            
            # Prüfen, ob wir Administratorrechte haben (für UAC-geschützte Ordner)
            def is_admin():
                try:
                    return ctypes.windll.shell32.IsUserAnAdmin()
                except:
                    return False
            
            if enable:
                # Erstelle eine .bat-Datei im Autostart-Verzeichnis
                try:
                    # Prüfe, ob eine eventuell vorhandene Datei gelöscht werden kann
                    if os.path.exists(bat_path) and not os.access(bat_path, os.W_OK):
                        raise PermissionError(f"Keine Schreibrechte für die vorhandene Datei: {bat_path}")
                        
                    # Versuche die Datei zu schreiben
                    try:
                        with open(bat_path, 'w') as f:
                            f.write(f'start "" "{app_path}"')
                        print(f"Autostart-Datei erfolgreich erstellt: {bat_path}")
                    except PermissionError:
                        if not is_admin():
                            raise Exception("Keine ausreichenden Berechtigungen. Versuchen Sie, das Programm als Administrator auszuführen.")
                        else:
                            raise Exception(f"Keine Schreibrechte für: {bat_path}")
                    except IOError as e:
                        raise Exception(f"IO-Fehler beim Schreiben der Datei: {e}")
                except Exception as e:
                    raise Exception(f"Fehler beim Erstellen der Autostart-Datei: {e}")
            else:
                # Entferne die Datei aus dem Autostart-Verzeichnis
                try:
                    if os.path.exists(shortcut_path):
                        try:
                            os.remove(shortcut_path)
                            print(f"Shortcut erfolgreich entfernt: {shortcut_path}")
                        except PermissionError:
                            if not is_admin():
                                raise Exception("Keine ausreichenden Berechtigungen zum Entfernen der Datei. Versuchen Sie, das Programm als Administrator auszuführen.")
                            else:
                                raise Exception(f"Keine Löschrechte für: {shortcut_path}")
                    
                    if os.path.exists(bat_path):
                        try:
                            os.remove(bat_path)
                            print(f"Batch-Datei erfolgreich entfernt: {bat_path}")
                        except PermissionError:
                            if not is_admin():
                                raise Exception("Keine ausreichenden Berechtigungen zum Entfernen der Datei. Versuchen Sie, das Programm als Administrator auszuführen.")
                            else:
                                raise Exception(f"Keine Löschrechte für: {bat_path}")
                except Exception as e:
                    raise Exception(f"Fehler beim Entfernen der Autostart-Datei: {e}")
        except Exception as e:
            # Alle Fehler auf eine höhere Ebene weitergeben
            print(f"Autostart-Konfiguration fehlgeschlagen: {e}")
            raise

class MainWindow(QMainWindow):
    """Hauptfenster der Anwendung"""
    
    def __init__(self):
        """Initialisiert das Hauptfenster"""
        super().__init__()
        
        # Fenstertitel und Größe - wir erstellen ein echtes Fenster
        self.setWindowTitle("BetterFinder")
        self.resize(300, 200)  # Sichtbares, kleines Fenster
        
        # Einstellungen laden
        self.settings = QSettings("BetterFinder", "BetterFinder")
        self.restore_settings()
        
        # Komponenten initialisieren
        self.init_core_components()
        
        # Zentrales Widget mit Info-Text
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        info_label = QLabel("BetterFinder läuft im Hintergrund.\nDrücken Sie Strg+Leertaste, um die Suche zu öffnen.")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        self.setCentralWidget(central_widget)
        
        # Systemtray-Icon
        self.setup_tray_icon()
        
        # Spotlight-Fenster
        self.spotlight = SpotlightWindow(self.indexer, self.search_engine)
        
        # Hotkey zum Öffnen (Strg+Space)
        self.setup_global_hotkey()
        
        # Indexierung starten
        self.start_indexing()
        
        # Spotlight-Fenster sofort anzeigen
        QTimer.singleShot(500, self.show_spotlight)
        
        # Zeige das Fenster zunächst an, damit das Tray-Icon richtig registriert wird
        self.show()
        # Warte kurz und minimiere dann
        QTimer.singleShot(2000, self.hide_to_tray)
    
    def hide_to_tray(self):
        """Versteckt das Fenster in den Tray"""
        self.hide()
        if self.tray_icon.isVisible():
            self.tray_icon.showMessage("BetterFinder", "BetterFinder läuft im Hintergrund.\nStrg+Leertaste drücken, um zu suchen", QSystemTrayIcon.Information, 5000)
    
    def init_core_components(self):
        """Initialisiert die Kernkomponenten (Indexer, Suchmaschine)"""
        try:
            # Pfad zur Indexdatenbank
            db_path = os.path.join(os.path.expanduser("~"), "BetterFinder", "index.db")
            
            # Verzeichnis erstellen, falls es nicht existiert
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Kernkomponenten
            self.indexer = FileSystemIndexer(db_path)
            self.search_engine = SearchEngine(db_path)
            
            # Thread-Variablen
            self.indexing_thread = None
        except Exception as e:
            # Fehlerbehandlung, falls Komponenten nicht initialisiert werden können
            print(f"Fehler bei der Initialisierung der Komponenten: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Kritischer Fehler", 
                                f"BetterFinder konnte nicht initialisiert werden: {str(e)}")
            sys.exit(1)
    
    def setup_tray_icon(self):
        """Richtet das Systemtray-Icon ein"""
        try:
            self.tray_icon = QSystemTrayIcon(self)
            
            # Versuche das BetterFinder-Icon zu laden
            icon_paths = [
                "BetterFinder-Icon.png",                               # Im Hauptverzeichnis
                os.path.join(os.getcwd(), "BetterFinder-Icon.png"),    # Absoluter Pfad
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "BetterFinder-Icon.png") # Relativer Pfad von der Klasse
            ]
            
            icon_set = False
            for path in icon_paths:
                if os.path.exists(path):
                    try:
                        print(f"Versuche Icon zu laden: {path}")
                        self.tray_icon.setIcon(QIcon(path))
                        icon_set = True
                        print(f"BetterFinder-Icon erfolgreich geladen von: {path}")
                        break
                    except Exception as e:
                        print(f"Fehler beim Laden des Icons von {path}: {e}")
            
            if not icon_set:
                # Fallback: Systemicon verwenden
                print("Konnte BetterFinder-Icon nicht laden, verwende System-Icon als Fallback")
                system_icon = QApplication.style().standardIcon(QApplication.style().SP_DialogHelpButton)
                self.tray_icon.setIcon(system_icon)
            
            # Tray-Menü
            tray_menu = QMenu()
            
            # Aktionen
            open_action = QAction("BetterFinder öffnen", self)
            open_action.triggered.connect(self.show_spotlight)
            
            reindex_action = QAction("Neu indizieren", self)
            reindex_action.triggered.connect(self.start_indexing)
            
            settings_action = QAction("Einstellungen", self)
            settings_action.triggered.connect(self.show_settings)
            
            exit_action = QAction("Beenden", self)
            exit_action.triggered.connect(self.close_application)
            
            # Aktionen zum Menü hinzufügen
            tray_menu.addAction(open_action)
            tray_menu.addSeparator()
            tray_menu.addAction(reindex_action)
            tray_menu.addAction(settings_action)
            tray_menu.addSeparator()
            tray_menu.addAction(exit_action)
            
            # Menü setzen und Icon anzeigen
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
            # Icon-Klick verbinden
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
            
            print(f"Tray-Icon sichtbar: {self.tray_icon.isVisible()}")
            if not self.tray_icon.isVisible():
                print("WARNUNG: Tray-Icon ist nicht sichtbar!")
            
        except Exception as e:
            # Falls Systemtray nicht unterstützt wird
            print(f"Systemtray wird nicht unterstützt: {e}")
            traceback.print_exc()
    
    def setup_global_hotkey(self):
        """Richtet globalen Hotkey ein"""
        self.shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        self.shortcut.activated.connect(self.show_spotlight)
    
    def on_tray_icon_activated(self, reason):
        """
        Behandelt Klicks auf das Tray-Icon
        
        Args:
            reason: Grund für die Aktivierung
        """
        if reason == QSystemTrayIcon.DoubleClick or reason == QSystemTrayIcon.Trigger:
            self.show_spotlight()
    
    def show_spotlight(self):
        """Zeigt das Spotlight-Fenster an"""
        if not self.spotlight.isVisible():
            self.spotlight.show()
            self.spotlight.search_bar.set_focus()
    
    def start_indexing(self):
        """Startet die Indizierung des Dateisystems"""
        if self.indexing_thread and self.indexing_thread.isRunning():
            self.tray_icon.showMessage("BetterFinder", "Indizierung läuft bereits...", QSystemTrayIcon.Information, 3000)
            return
        
        self.tray_icon.showMessage("BetterFinder", "Indizierung gestartet...", QSystemTrayIcon.Information, 3000)
        
        self.indexing_thread = IndexingThread(self.indexer)
        self.indexing_thread.progress.connect(self.update_status)
        self.indexing_thread.finished_indexing.connect(self.on_indexing_finished)
        self.indexing_thread.error_occurred.connect(self.show_error)
        self.indexing_thread.start()
    
    def on_indexing_finished(self):
        """Wird aufgerufen, wenn die Indizierung abgeschlossen ist"""
        self.update_status("Indizierung abgeschlossen.")
        self.tray_icon.showMessage("BetterFinder", "Indizierung abgeschlossen", QSystemTrayIcon.Information, 3000)
    
    def update_status(self, message: str):
        """
        Aktualisiert den Status
        
        Args:
            message: Anzuzeigende Nachricht
        """
        print(f"Status: {message}")
        # Könnte auch in einem Label im Spotlight-Fenster angezeigt werden
    
    def show_error(self, error_message: str):
        """
        Zeigt eine Fehlermeldung an
        
        Args:
            error_message: Anzuzeigende Fehlermeldung
        """
        self.tray_icon.showMessage("BetterFinder Fehler", error_message, QSystemTrayIcon.Critical, 5000)
    
    def show_settings(self):
        """Zeigt die Einstellungen an"""
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Einstellungen wurden gespeichert
            # Aktualisiere die Anwendung mit den neuen Einstellungen
            self.apply_settings()
    
    def apply_settings(self):
        """Wende die gespeicherten Einstellungen an"""
        settings = QSettings("BetterFinder", "BetterFinder")
        
        # Hotkey
        hotkey = settings.value("hotkey", "Strg+Leertaste")
        # In einer richtigen Implementierung würde hier der Hotkey aktualisiert
        
        # Maximale Anzahl der Ergebnisse
        max_results = settings.value("max_results", 30, type=int)
        # Setze die maximale Anzahl der Ergebnisse für die Suche
        
        # Ausgeschlossene Verzeichnisse
        excluded_paths = settings.value("excluded_paths", [], type=list)
        # Aktualisiere die Liste der ausgeschlossenen Verzeichnisse im Indexer
        
        # Benachrichtigung anzeigen
        self.tray_icon.showMessage(
            "BetterFinder", 
            "Einstellungen wurden aktualisiert.", 
            QSystemTrayIcon.Information, 
            3000
        )
    
    def close_application(self):
        """Schließt die Anwendung"""
        self.save_settings()
        QApplication.quit()
    
    def closeEvent(self, event):
        """
        Wird aufgerufen, wenn das Fenster geschlossen wird
        
        Args:
            event: Close-Event
        """
        # Minimieren statt schließen, wenn nicht explizit beendet
        if self.tray_icon.isVisible():
            # Tray ist sichtbar, also minimieren
            event.ignore()
            self.hide()
        else:
            # Kein Tray, also normal schließen
            self.save_settings()
            event.accept()
    
    def save_settings(self):
        """Speichert die Einstellungen"""
        # Einstellungen könnten hier gespeichert werden
        pass
    
    def restore_settings(self):
        """Stellt die Einstellungen wieder her"""
        # Einstellungen könnten hier wiederhergestellt werden
        pass

def main():
    """Haupteinstiegspunkt für die Anwendung"""
    app = QApplication(sys.argv)
    app.setApplicationName("BetterFinder")
    app.setOrganizationName("BetterFinder")
    
    # Dunkles Theme für die gesamte Anwendung
    app.setStyle("Fusion")
    
    # Dunkle Palette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(BACKGROUND_COLOR))
    dark_palette.setColor(QPalette.WindowText, QColor(TEXT_COLOR))
    dark_palette.setColor(QPalette.Base, QColor(SECONDARY_COLOR))
    dark_palette.setColor(QPalette.AlternateBase, QColor(BACKGROUND_COLOR))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(TEXT_COLOR))
    dark_palette.setColor(QPalette.ToolTipText, QColor(TEXT_COLOR))
    dark_palette.setColor(QPalette.Text, QColor(TEXT_COLOR))
    dark_palette.setColor(QPalette.Button, QColor(SECONDARY_COLOR))
    dark_palette.setColor(QPalette.ButtonText, QColor(TEXT_COLOR))
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(HIGHLIGHT_COLOR))
    dark_palette.setColor(QPalette.Highlight, QColor(HIGHLIGHT_COLOR))
    dark_palette.setColor(QPalette.HighlightedText, Qt.white)
    
    app.setPalette(dark_palette)
    
    # Hauptfenster erstellen (im Hintergrund)
    window = MainWindow()
    
    # Anwendung starten
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 