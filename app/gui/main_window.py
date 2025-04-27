"""
Main window of the application

This module defines the main window of the application with:
1. Spotlight-like search interface
2. Tray icon with settings and reindexing
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

# Constant definitions for styling
BACKGROUND_COLOR = "#202020"
TEXT_COLOR = "#FFFFFF"
HIGHLIGHT_COLOR = "#0078D7"
SECONDARY_COLOR = "#303030"
BORDER_COLOR = "#404040"
ICON_COLOR = "#808080"

# Command prefixes
COMMANDS = {
    "=": "Calculates mathematical expressions",
    "!": "Accesses previous results",
    "?": "Searches for files and folders",
    "@": "Opens settings and options",
    ".": "Searches for programs"
}

class SearchThread(QThread):
    """Thread for searching, to avoid blocking the UI"""
    
    # Signal that returns the search results
    results_ready = pyqtSignal(list)
    # Signal for errors
    error_occurred = pyqtSignal(str)
    
    def __init__(self, search_engine: SearchEngine, query: str, file_type: Optional[str] = None):
        """
        Initializes the search thread
        
        Args:
            search_engine: The search engine
            query: The search query
            file_type: Optional file type filter
        """
        super().__init__()
        self.search_engine = search_engine
        self.query = query
        self.file_type = file_type
        self.stop_requested = False
    
    def run(self):
        """Performs the search"""
        try:
            # Early check for cancellation
            if self.stop_requested:
                return
                
            # Check if it's a regular expression
            if self.query.startswith('regex:'):
                regex_pattern = self.query[6:].strip()
                results = self.search_engine.search_by_regex(regex_pattern, self.file_type)
            # Check for command prefixes
            elif self.query.startswith('='):
                # Mathematical expression
                try:
                    expression = self.query[1:].strip()
                    result = eval(expression, {"__builtins__": {}}, {})
                    results = [{"filename": f"{expression} = {result}", "path": "Calculation", 
                              "size": 0, "last_modified": datetime.now(), "full_path": str(result),
                              "type": "calculation"}]
                except:
                    results = []
            elif self.query.startswith('@'):
                # Show settings
                cmd = self.query[1:].strip().lower()
                results = [{"filename": "Open Settings", "path": "BetterFinder", 
                          "size": 0, "last_modified": datetime.now(), "full_path": "settings",
                          "type": "command"}]
            else:
                results = self.search_engine.search(self.query, self.file_type)
            
            # Send results back if no cancellation was requested
            if not self.stop_requested:
                self.results_ready.emit(results)
        except Exception as e:
            # Send error signal if no cancellation was requested
            if not self.stop_requested:
                error_msg = f"Search error: {str(e)}"
                self.error_occurred.emit(error_msg)
                # Return empty results list
                self.results_ready.emit([])
            # Output complete error info in terminal
            print(f"Search error: {e}")
            traceback.print_exc()
    
    def stop(self):
        """Requests thread cancellation"""
        self.stop_requested = True

class IndexingThread(QThread):
    """Thread for indexing the file system"""
    
    # Signal for progress
    progress = pyqtSignal(str)
    # Signal for completion
    finished_indexing = pyqtSignal()
    # Signal for errors
    error_occurred = pyqtSignal(str)
    
    def __init__(self, indexer: FileSystemIndexer):
        """
        Initializes the indexing thread
        
        Args:
            indexer: The file system indexer
        """
        super().__init__()
        self.indexer = indexer
    
    def run(self):
        """Performs the indexing"""
        try:
            self.progress.emit("Indexing started...")
            self.indexer.start_indexing()
            self.progress.emit("Indexing completed.")
            self.finished_indexing.emit()
        except Exception as e:
            # Send error signal
            error_msg = f"Indexing error: {str(e)}"
            self.error_occurred.emit(error_msg)
            self.progress.emit("Indexing failed.")
            # Output complete error info in terminal
            print(f"Indexing error: {e}")
            traceback.print_exc()

class SpotlightStyleSearchBar(QWidget):
    """Spotlight-like search bar"""
    
    search_triggered = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Search field container for radius effect
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
        
        # Layout for the container
        container_layout = QHBoxLayout(search_container)
        container_layout.setContentsMargins(15, 0, 15, 0)
        
        # Search field
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search...")
        self.search_box.setMinimumHeight(50)
        
        # Transparent search field within the container
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                color: {TEXT_COLOR};
                border: none;
                font-size: 16px;
                padding: 4px;
            }}
        """)
        
        # Add to container layout
        container_layout.addWidget(self.search_box)
        
        # Container to main layout
        layout.addWidget(search_container)
        
        # Signals
        self.search_box.returnPressed.connect(self.emit_search)
        self.search_box.textChanged.connect(self.on_text_changed)
        
        # Layout set
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
    """List of search results in Spotlight style"""
    
    item_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Styling
        self.setFrameShape(QFrame.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container for the results list
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
        
        # Signals
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
        
    def on_item_double_clicked(self, item):
        data = item.data(Qt.UserRole)
        if data:
            self.item_selected.emit(data)

class SpotlightWindow(QDialog):
    """Main window in Spotlight style"""
    
    def __init__(self, indexer, search_engine):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        self.indexer = indexer
        self.search_engine = search_engine
        
        # Search thread
        self.search_thread = None
        
        # Timer for delayed search
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        # Disable shadows for true transparency
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.init_ui()
        
    def init_ui(self):
        # Position and size
        screen_geometry = QDesktopWidget().availableGeometry()
        width = min(600, screen_geometry.width() - 100)
        height = 500
        
        x = (screen_geometry.width() - width) // 2
        y = screen_geometry.height() // 4
        
        self.setGeometry(x, y, width, height)
        
        # Content of the window
        self.content_widget = QWidget(self)
        self.content_widget.setObjectName("contentWidget")
        
        # Extremely rounded corners for the content
        self.content_widget.setStyleSheet(f"""
            #contentWidget {{
                background-color: {BACKGROUND_COLOR};
                border-radius: 35px;
                border: 1px solid {BORDER_COLOR};
            }}
        """)
        
        # Layout for the entire window (transparent background)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)  # Space for shadow
        main_layout.addWidget(self.content_widget)
        
        # Layout for the content
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)
        
        # Shadow effect for the content
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.content_widget.setGraphicsEffect(shadow)
        
        # Search bar
        self.search_bar = SpotlightStyleSearchBar()
        self.search_bar.search_triggered.connect(self.on_search_triggered)
        content_layout.addWidget(self.search_bar)
        
        # Results list
        self.results_list = SpotlightResultsList()
        self.results_list.item_selected.connect(self.on_item_selected)
        content_layout.addWidget(self.results_list)
        
        # Focus on search field
        self.search_bar.set_focus()
    
    def keyPressEvent(self, event):
        # Escape closes the window
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)
            
    def mousePressEvent(self, event):
        # Window can be moved
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        # Move window
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def on_search_triggered(self, text):
        # Start delayed search
        self.search_timer.start(300)
        
    def stop_current_search(self):
        """Stops the current search thread if it exists"""
        if self.search_thread and self.search_thread.isRunning():
            if hasattr(self.search_thread, 'stop'):
                self.search_thread.stop()
            
            self.search_thread.disconnect()
            self.search_thread.terminate()
            self.search_thread.wait(500)
            self.search_thread = None
    
    def perform_search(self):
        """Performs the actual search"""
        query = self.search_bar.get_text()
        
        # Check if search text is empty
        if not query:
            self.results_list.clear()
            return
        
        # Stop current thread
        self.stop_current_search()
        
        # Start new search thread
        self.search_thread = SearchThread(self.search_engine, query, None)
        self.search_thread.results_ready.connect(self.display_results)
        self.search_thread.error_occurred.connect(self.show_error)
        self.search_thread.start()
    
    def display_results(self, results):
        """Shows the search results"""
        self.results_list.clear()
        
        for result in results:
            item = QListWidgetItem()
            
            # Item text and icon based on type
            if 'type' in result and result['type'] == 'calculation':
                item.setText(result['filename'])
                # Math symbol for calculations
                # (here a real icon should be set)
            elif 'type' in result and result['type'] == 'command':
                item.setText(result['filename'])
                # Settings symbol for commands
                # (here a real icon should be set)
            else:
                # Normal file
                item.setText(f"{result['filename']} - {result['path']}")
                # File type-dependent icon
                # (here a real icon should be set)
            
            # Data for double click storage
            item.setData(Qt.UserRole, result['full_path'])
            
            self.results_list.addItem(item)
    
    def on_item_selected(self, path):
        """Handles selection of a result"""
        if path == 'settings':
            # Open settings
            self.hide()
            return
            
        try:
            # Open file
            open_file(path)
            self.hide()
        except Exception as e:
            self.show_error(f"Error opening file: {str(e)}")
    
    def show_error(self, error_message):
        """Shows an error message"""
        print(f"Error: {error_message}")
        # Here a error icon could be displayed in the results list

class SettingsDialog(QDialog):
    """Settings dialog for BetterFinder"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("BetterFinder", "BetterFinder")
        self.setWindowTitle("BetterFinder Settings")
        self.resize(500, 400)
        
        # Transparent background for rounding
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Create UI
        self.init_ui()
        
        # Load existing settings
        self.load_settings()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Container for content
        self.content_widget = QWidget(self)
        self.content_widget.setObjectName("settingsContent")
        self.content_widget.setStyleSheet(f"""
            #settingsContent {{
                background-color: {BACKGROUND_COLOR};
                border-radius: 25px;
                border: 1px solid {BORDER_COLOR};
            }}
        """)
        
        # Content layout
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(15)
        
        # Title
        title_label = QLabel("BetterFinder Settings")
        title_label.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 18px; font-weight: bold;")
        content_layout.addWidget(title_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"background-color: {BORDER_COLOR};")
        content_layout.addWidget(separator)
        
        # Scroll area for all settings
        scroll_area = QWidget()
        scroll_layout = QVBoxLayout(scroll_area)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(15)
        
        # 1. Hotkey setting
        hotkey_group = QGroupBox("Hotkey")
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
        hotkey_description = QLabel("Hotkey to open BetterFinder:")
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
        
        self.hotkey_button = QPushButton("Change")
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
        
        # 2. Autostart option
        autostart_group = QGroupBox("System start")
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
        self.autostart_checkbox = QCheckBox("Start BetterFinder automatically at system start")
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
        
        # 3. Excluded directories
        exclude_group = QGroupBox("Excluded directories")
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
        exclude_description = QLabel("These directories will not be indexed:")
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
        self.add_exclude_button = QPushButton("Add")
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
        
        self.remove_exclude_button = QPushButton("Remove")
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
        
        # 4. Maximum number of results
        results_group = QGroupBox("Results")
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
        results_description = QLabel("Maximum number of displayed search results:")
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
        
        # Add all groups to scroll layout
        scroll_layout.addWidget(hotkey_group)
        scroll_layout.addWidget(autostart_group)
        scroll_layout.addWidget(exclude_group)
        scroll_layout.addWidget(results_group)
        scroll_layout.addStretch(1)
        
        # Add scroll widget to content layout
        content_layout.addWidget(scroll_area)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        self.cancel_button = QPushButton("Cancel")
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
        
        self.save_button = QPushButton("Save")
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
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.content_widget.setGraphicsEffect(shadow)
        
        # Add content to main layout
        main_layout.addWidget(self.content_widget)
    
    def load_settings(self):
        """Load existing settings"""
        # Hotkey
        hotkey = self.settings.value("hotkey", "Strg+Leertaste")
        self.hotkey_edit.setText(hotkey)
        
        # Autostart
        autostart = self.settings.value("autostart", False, type=bool)
        self.autostart_checkbox.setChecked(autostart)
        
        # Excluded directories
        excluded_paths = self.settings.value("excluded_paths", [], type=list)
        for path in excluded_paths:
            self.exclude_list.addItem(path)
        
        # Maximum number of results
        max_results = self.settings.value("max_results", 30, type=int)
        self.results_spinbox.setValue(max_results)
    
    def save_settings(self):
        """Saves the settings"""
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
                print(f"Error configuring autostart: {e}")
                # Show warning, but don't abort
                QMessageBox.warning(self, "Autostart warning",
                                  f"Autostart setting could not be applied: {e}\n\nAll other settings were saved.")
            
            # Excluded directories
            excluded_paths = []
            for i in range(self.exclude_list.count()):
                excluded_paths.append(self.exclude_list.item(i).text())
            self.settings.setValue("excluded_paths", excluded_paths)
            
            # Maximum number of results
            self.settings.setValue("max_results", self.results_spinbox.value())
            
            # Save settings
            self.settings.sync()
            
            # Close dialog
            self.accept()
        except Exception as e:
            # Show error message and don't abort
            print(f"Error saving settings: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", 
                              f"Settings could not be saved: {str(e)}")
            # Dialog remains open so user can try again
    
    def change_hotkey(self):
        """Changes the hotkey"""
        # In a real implementation, here a dialog would be displayed,
        # which captures a key press and stores it as the new hotkey
        self.hotkey_edit.setText("Strg+Leertaste")  # Placeholder, would be replaced in reality by the captured hotkey
    
    def add_exclude_path(self):
        """Adds an excluded path"""
        directory = QFileDialog.getExistingDirectory(self, "Select directory")
        if directory:
            # Check if the path is already in the list
            for i in range(self.exclude_list.count()):
                if self.exclude_list.item(i).text() == directory:
                    return
            
            # Add the path to the list
            self.exclude_list.addItem(directory)
    
    def remove_exclude_path(self):
        """Removes a selected path"""
        selected_items = self.exclude_list.selectedItems()
        for item in selected_items:
            self.exclude_list.takeItem(self.exclude_list.row(item))
    
    def setup_autostart(self, enable):
        """Configures autostart"""
        import os
        import sys
        import ctypes
        
        try:
            # Path to the executable
            if getattr(sys, 'frozen', False):
                # If the application was created with PyInstaller
                app_path = sys.executable
            else:
                # If the application is run with Python
                app_path = os.path.abspath(sys.argv[0])
            
            # Autostart directory
            startup_dir = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            shortcut_path = os.path.join(startup_dir, 'BetterFinder.lnk')
            bat_path = os.path.join(startup_dir, 'BetterFinder.bat')
            
            # Check if the directory exists and is writable
            if not os.path.exists(startup_dir):
                os.makedirs(startup_dir, exist_ok=True)
                print(f"Autostart directory created: {startup_dir}")
            
            # Check if the directory is writable
            if not os.access(startup_dir, os.W_OK):
                raise Exception(f"No write permissions for the autostart directory: {startup_dir}")
            
            # Check if we have administrator rights (for UAC-protected folders)
            def is_admin():
                try:
                    return ctypes.windll.shell32.IsUserAnAdmin()
                except:
                    return False
            
            if enable:
                # Create a .bat file in the autostart directory
                try:
                    # Check if an existing file can be deleted
                    if os.path.exists(bat_path) and not os.access(bat_path, os.W_OK):
                        raise PermissionError(f"No write permissions for the existing file: {bat_path}")
                        
                    # Try to write the file
                    try:
                        with open(bat_path, 'w') as f:
                            f.write(f'start "" "{app_path}"')
                        print(f"Autostart file created successfully: {bat_path}")
                    except PermissionError:
                        if not is_admin():
                            raise Exception("Not enough permissions. Try running the program as Administrator.")
                        else:
                            raise Exception(f"No write permissions for: {bat_path}")
                    except IOError as e:
                        raise Exception(f"IO error when writing file: {e}")
                except Exception as e:
                    raise Exception(f"Error creating autostart file: {e}")
            else:
                # Remove the file from the autostart directory
                try:
                    if os.path.exists(shortcut_path):
                        try:
                            os.remove(shortcut_path)
                            print(f"Shortcut removed successfully: {shortcut_path}")
                        except PermissionError:
                            if not is_admin():
                                raise Exception("Not enough permissions to remove the file. Try running the program as Administrator.")
                            else:
                                raise Exception(f"No delete permissions for: {shortcut_path}")
                    
                    if os.path.exists(bat_path):
                        try:
                            os.remove(bat_path)
                            print(f"Batch file removed successfully: {bat_path}")
                        except PermissionError:
                            if not is_admin():
                                raise Exception("Not enough permissions to remove the file. Try running the program as Administrator.")
                            else:
                                raise Exception(f"No delete permissions for: {bat_path}")
                except Exception as e:
                    raise Exception(f"Error removing autostart file: {e}")
        except Exception as e:
            # Pass all errors to a higher level
            print(f"Autostart configuration failed: {e}")
            raise

class MainWindow(QMainWindow):
    """Main window of the application"""
    
    def __init__(self):
        """Initializes the main window"""
        super().__init__()
        
        # Window title and size - we create a real window
        self.setWindowTitle("BetterFinder")
        self.resize(300, 200)  # Visible, small window
        
        # Load settings
        self.settings = QSettings("BetterFinder", "BetterFinder")
        self.restore_settings()
        
        # Initialize components
        self.init_core_components()
        
        # Central widget with info text
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        info_label = QLabel("BetterFinder running in the background.\nPress Ctrl+Space to open the search.")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        self.setCentralWidget(central_widget)
        
        # System tray icon
        self.setup_tray_icon()
        
        # Spotlight window
        self.spotlight = SpotlightWindow(self.indexer, self.search_engine)
        
        # Hotkey to open (Ctrl+Space)
        self.setup_global_hotkey()
        
        # Start indexing
        self.start_indexing()
        
        # Show spotlight window immediately
        QTimer.singleShot(500, self.show_spotlight)
        
        # Show the window first so the tray icon registers correctly
        self.show()
        # Wait briefly and minimize then
        QTimer.singleShot(2000, self.hide_to_tray)
    
    def hide_to_tray(self):
        """Hides the window in the tray"""
        self.hide()
        if self.tray_icon.isVisible():
            self.tray_icon.showMessage("BetterFinder", "BetterFinder running in the background.\nPress Ctrl+Space to search", QSystemTrayIcon.Information, 5000)
    
    def init_core_components(self):
        """Initializes the core components (indexer, search engine)"""
        try:
            # Path to index database
            db_path = os.path.join(os.path.expanduser("~"), "BetterFinder", "index.db")
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Core components
            self.indexer = FileSystemIndexer(db_path)
            self.search_engine = SearchEngine(db_path)
            
            # Thread variables
            self.indexing_thread = None
        except Exception as e:
            # Error handling if components cannot be initialized
            print(f"Error initializing components: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Critical error", 
                                f"BetterFinder could not be initialized: {str(e)}")
            sys.exit(1)
    
    def setup_tray_icon(self):
        """Sets up the system tray icon"""
        try:
            self.tray_icon = QSystemTrayIcon(self)
            
            # Try to load the BetterFinder icon
            icon_paths = [
                "BetterFinder-Icon.png",                               # In main directory
                os.path.join(os.getcwd(), "BetterFinder-Icon.png"),    # Absolute path
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "BetterFinder-Icon.png") # Relative path from class
            ]
            
            icon_set = False
            for path in icon_paths:
                if os.path.exists(path):
                    try:
                        print(f"Trying to load icon: {path}")
                        self.tray_icon.setIcon(QIcon(path))
                        icon_set = True
                        print(f"BetterFinder icon loaded successfully from: {path}")
                        break
                    except Exception as e:
                        print(f"Error loading icon from {path}: {e}")
            
            if not icon_set:
                # Fallback: Use system icon
                print("Could not load BetterFinder icon, use system icon as fallback")
                system_icon = QApplication.style().standardIcon(QApplication.style().SP_DialogHelpButton)
                self.tray_icon.setIcon(system_icon)
            
            # Tray menu
            tray_menu = QMenu()
            
            # Actions
            open_action = QAction("Open BetterFinder", self)
            open_action.triggered.connect(self.show_spotlight)
            
            reindex_action = QAction("Reindex", self)
            reindex_action.triggered.connect(self.start_indexing)
            
            settings_action = QAction("Settings", self)
            settings_action.triggered.connect(self.show_settings)
            
            exit_action = QAction("Exit", self)
            exit_action.triggered.connect(self.close_application)
            
            # Add actions to menu
            tray_menu.addAction(open_action)
            tray_menu.addSeparator()
            tray_menu.addAction(reindex_action)
            tray_menu.addAction(settings_action)
            tray_menu.addSeparator()
            tray_menu.addAction(exit_action)
            
            # Set menu and show icon
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
            # Icon click connection
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
            
            print(f"Tray icon visible: {self.tray_icon.isVisible()}")
            if not self.tray_icon.isVisible():
                print("WARNING: Tray icon is not visible!")
            
        except Exception as e:
            # If system tray is not supported
            print(f"System tray is not supported: {e}")
            traceback.print_exc()
    
    def setup_global_hotkey(self):
        """Sets up the global hotkey"""
        self.shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        self.shortcut.activated.connect(self.show_spotlight)
    
    def on_tray_icon_activated(self, reason):
        """
        Handles clicks on the tray icon
        
        Args:
            reason: Reason for activation
        """
        if reason == QSystemTrayIcon.DoubleClick or reason == QSystemTrayIcon.Trigger:
            self.show_spotlight()
    
    def show_spotlight(self):
        """Shows the spotlight window"""
        if not self.spotlight.isVisible():
            self.spotlight.show()
            self.spotlight.search_bar.set_focus()
    
    def start_indexing(self):
        """Starts indexing the file system"""
        if self.indexing_thread and self.indexing_thread.isRunning():
            self.tray_icon.showMessage("BetterFinder", "Indexing already running...", QSystemTrayIcon.Information, 3000)
            return
        
        self.tray_icon.showMessage("BetterFinder", "Indexing started...", QSystemTrayIcon.Information, 3000)
        
        self.indexing_thread = IndexingThread(self.indexer)
        self.indexing_thread.progress.connect(self.update_status)
        self.indexing_thread.finished_indexing.connect(self.on_indexing_finished)
        self.indexing_thread.error_occurred.connect(self.show_error)
        self.indexing_thread.start()
    
    def on_indexing_finished(self):
        """Called when indexing is completed"""
        self.update_status("Indexing completed.")
        self.tray_icon.showMessage("BetterFinder", "Indexing completed", QSystemTrayIcon.Information, 3000)
    
    def update_status(self, message: str):
        """
        Updates the status
        
        Args:
            message: Message to display
        """
        print(f"Status: {message}")
        # Could also be displayed in a label in the spotlight window
    
    def show_error(self, error_message: str):
        """
        Shows an error message
        
        Args:
            error_message: Message to display
        """
        self.tray_icon.showMessage("BetterFinder Error", error_message, QSystemTrayIcon.Critical, 5000)
    
    def show_settings(self):
        """Shows the settings"""
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Settings were saved
            # Update application with new settings
            self.apply_settings()
    
    def apply_settings(self):
        """Applies the saved settings"""
        settings = QSettings("BetterFinder", "BetterFinder")
        
        # Hotkey
        hotkey = settings.value("hotkey", "Strg+Leertaste")
        # In a real implementation, here the hotkey would be updated
        
        # Maximum number of results
        max_results = settings.value("max_results", 30, type=int)
        # Set the maximum number of results for the search
        
        # Excluded directories
        excluded_paths = settings.value("excluded_paths", [], type=list)
        # Update the list of excluded directories in the indexer
        
        # Show notification
        self.tray_icon.showMessage(
            "BetterFinder", 
            "Settings updated.", 
            QSystemTrayIcon.Information, 
            3000
        )
    
    def close_application(self):
        """Closes the application"""
        self.save_settings()
        QApplication.quit()
    
    def closeEvent(self, event):
        """
        Called when the window is closed
        
        Args:
            event: Close event
        """
        # Minimize instead of closing if not explicitly ended
        if self.tray_icon.isVisible():
            # Tray is visible, so minimize
            event.ignore()
            self.hide()
        else:
            # No tray, so normal close
            self.save_settings()
            event.accept()
    
    def save_settings(self):
        """Saves the settings"""
        # Settings could be saved here
        pass
    
    def restore_settings(self):
        """Restores the settings"""
        # Settings could be restored here
        pass

def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)
    app.setApplicationName("BetterFinder")
    app.setOrganizationName("BetterFinder")
    
    # Dark theme for the entire application
    app.setStyle("Fusion")
    
    # Dark palette
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
    
    # Main window create (in background)
    window = MainWindow()
    
    # Application start
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 