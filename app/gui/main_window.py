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
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings, QSize, QRect, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence, QFont, QColor, QPalette, QFontMetrics, QRegion, QPainterPath

from app.core.indexer import FileSystemIndexer
from app.core.search_engine import SearchEngine
from app.utils.file_utils import get_file_size_str, get_file_date_str, open_file, open_containing_folder

# Constant definitions for styling - MODERN UI UPGRADE
BACKGROUND_COLOR = "#1a1a1a"  # Darker, more modern
BACKGROUND_SECONDARY = "#2d2d2d"  # Secondary background
TEXT_COLOR = "#ffffff"
TEXT_SECONDARY = "#b3b3b3"  # Secondary text color
ACCENT_COLOR = "#007acc"  # Modern blue accent
ACCENT_HOVER = "#1e88e5"  # Hover state
SUCCESS_COLOR = "#4caf50"  # Success green
WARNING_COLOR = "#ff9800"  # Warning orange
ERROR_COLOR = "#f44336"  # Error red
BORDER_COLOR = "#404040"
BORDER_LIGHT = "#606060"  # Lighter border for hover states
SHADOW_COLOR = "rgba(0, 0, 0, 0.3)"
GLASS_BACKGROUND = "rgba(45, 45, 45, 0.8)"  # Glassmorphism effect

# Animation constants
ANIMATION_DURATION = 200  # ms
HOVER_ANIMATION_DURATION = 150  # ms

# Typography
FONT_FAMILY = "Segoe UI, Arial, sans-serif"
FONT_SIZE_LARGE = "18px"
FONT_SIZE_MEDIUM = "14px"
FONT_SIZE_SMALL = "12px"

# Spacing
SPACING_SMALL = 8
SPACING_MEDIUM = 16
SPACING_LARGE = 24
BORDER_RADIUS = 12
BORDER_RADIUS_LARGE = 20

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
        """Performs the search - IMPROVED WITH BETTER CANCELLATION"""
        try:
            # Early check for cancellation
            if self.stop_requested:
                print(f"Search cancelled before start: {self.query}")
                return
                
            print(f"Starting search for: '{self.query}'")
            
            # Check if it's a regular expression
            if self.query.startswith('regex:'):
                if self.stop_requested:
                    return
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
                # Check for cancellation before expensive search
                if self.stop_requested:
                    print(f"Search cancelled before engine call: {self.query}")
                    return
                results = self.search_engine.search(self.query, self.file_type)
            
            # Final check for cancellation before emitting results
            if not self.stop_requested:
                print(f"Search completed for '{self.query}': {len(results)} results")
                self.results_ready.emit(results)
            else:
                print(f"Search cancelled after completion: {self.query}")
                
        except Exception as e:
            # Send error signal if no cancellation was requested
            if not self.stop_requested:
                error_msg = f"Search error: {str(e)}"
                print(f"Search error for '{self.query}': {error_msg}")
                self.error_occurred.emit(error_msg)
                # Return empty results list
                self.results_ready.emit([])
            else:
                print(f"Search cancelled due to error: {self.query}")
            # Output complete error info in terminal
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
        
        # Search field container for radius effect - MODERN UPGRADE
        search_container = QWidget()
        search_container.setObjectName("searchContainer")
        search_container.setStyleSheet(f"""
            #searchContainer {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BACKGROUND_SECONDARY}, stop:1 {BACKGROUND_COLOR});
                border-radius: {BORDER_RADIUS_LARGE}px;
                border: 2px solid {BORDER_COLOR};
                padding: 0px;
            }}
            #searchContainer:focus-within {{
                border: 2px solid {ACCENT_COLOR};
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BACKGROUND_SECONDARY}, stop:1 #333333);
            }}
        """)
        
        # Layout for the container
        container_layout = QHBoxLayout(search_container)
        container_layout.setContentsMargins(20, 0, 20, 0)
        
        # Search icon (using Unicode symbol for now)
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: {FONT_SIZE_LARGE};
                padding: 0px 8px 0px 0px;
            }}
        """)
        container_layout.addWidget(search_icon)
        
        # Search field
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search files, folders, and more...")
        self.search_box.setMinimumHeight(60)
        
        # Modern search field styling
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                color: {TEXT_COLOR};
                border: none;
                font-family: {FONT_FAMILY};
                font-size: {FONT_SIZE_LARGE};
                font-weight: 400;
                padding: 4px;
            }}
            QLineEdit::placeholder {{
                color: {TEXT_SECONDARY};
                font-style: italic;
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
        
        # MODERN UI UPGRADE - Enhanced styling
        self.setStyleSheet(f"""
            #resultsList {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BACKGROUND_SECONDARY}, stop:1 {BACKGROUND_COLOR});
                color: {TEXT_COLOR};
                border: none;
                border-radius: {BORDER_RADIUS_LARGE}px;
                padding: {SPACING_MEDIUM}px;
                font-family: {FONT_FAMILY};
                selection-background-color: transparent;
            }}
            QListWidget::item {{
                border-radius: {BORDER_RADIUS}px;
                padding: {SPACING_MEDIUM}px {SPACING_LARGE}px;
                margin-bottom: 6px;
                min-height: 50px;
                border-left: 3px solid transparent;
                font-size: {FONT_SIZE_MEDIUM};
                background: transparent;
            }}
            QListWidget::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT_COLOR}, stop:1 {ACCENT_HOVER});
                color: white;
                border-left: 3px solid white;
                font-weight: 500;
            }}
            QListWidget::item:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {BACKGROUND_SECONDARY}, stop:1 rgba(45, 45, 45, 0.8));
                border-left: 3px solid {ACCENT_COLOR};
            }}
            QListWidget::item:selected:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT_HOVER}, stop:1 {ACCENT_COLOR});
            }}
            QScrollBar:vertical {{
                border: none;
                background: {BACKGROUND_COLOR};
                width: 10px;
                margin: {SPACING_MEDIUM}px 3px {SPACING_MEDIUM}px 3px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {BORDER_COLOR}, stop:1 {BORDER_LIGHT});
                min-height: 30px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT_COLOR}, stop:1 {ACCENT_HOVER});
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
        super().__init__(None, Qt.FramelessWindowHint)
        
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
        
        # MODERN UI UPGRADE - Glassmorphism effect
        self.content_widget.setStyleSheet(f"""
            #contentWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {GLASS_BACKGROUND}, stop:1 {BACKGROUND_COLOR});
                border-radius: {BORDER_RADIUS_LARGE * 2}px;
                border: 2px solid {BORDER_COLOR};
                backdrop-filter: blur(20px);
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
        
        # MODERN UI UPGRADE - Add fade-in animation
        self.setWindowOpacity(0.0)
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(ANIMATION_DURATION)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def showEvent(self, event):
        """Override show event to add animation"""
        super().showEvent(event)
        if hasattr(self, 'fade_animation'):
            self.fade_animation.start()
    
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
        # Start delayed search - IMPROVED DEBOUNCING
        if self.search_timer.isActive():
            self.search_timer.stop()
        
        # Only search if text is not empty
        if text.strip():
            self.search_timer.start(300)
        else:
            # Clear results immediately for empty search
            self.results_list.clear()
            self.stop_current_search()
        
    def stop_current_search(self):
        """Stops the current search thread if it exists - IMPROVED"""
        if self.search_thread and self.search_thread.isRunning():
            try:
                # Signal the thread to stop
                if hasattr(self.search_thread, 'stop'):
                    self.search_thread.stop()
                
                # Disconnect all signals to prevent race conditions
                self.search_thread.results_ready.disconnect()
                self.search_thread.error_occurred.disconnect()
                
                # Try graceful termination first
                self.search_thread.quit()
                if not self.search_thread.wait(1000):  # Wait max 1 second
                    # Force termination if needed
                    self.search_thread.terminate()
                    self.search_thread.wait(500)
                    
            except Exception as e:
                print(f"Error stopping search thread: {e}")
            finally:
                self.search_thread = None
    
    def perform_search(self):
        """Performs the actual search - IMPROVED THREAD SAFETY"""
        query = self.search_bar.get_text().strip()
        
        # Check if search text is empty
        if not query:
            self.results_list.clear()
            return
        
        # Prevent multiple searches with same query
        if hasattr(self, 'last_query') and self.last_query == query:
            return
        
        self.last_query = query
        
        # Stop current thread safely
        self.stop_current_search()
        
        # Small delay to ensure thread cleanup
        QTimer.singleShot(50, lambda: self._start_search_thread(query))
    
    def _start_search_thread(self, query):
        """Helper method to start search thread"""
        try:
            # Double-check that no thread is running
            if self.search_thread and self.search_thread.isRunning():
                print("Warning: Previous search thread still running")
                return
            
            # Create and start new search thread
            self.search_thread = SearchThread(self.search_engine, query, None)
            self.search_thread.results_ready.connect(self.display_results)
            self.search_thread.error_occurred.connect(self.show_error)
            self.search_thread.start()
            
            print(f"Started search for: '{query}'")
            
        except Exception as e:
            print(f"Error starting search thread: {e}")
            self.show_error(f"Search error: {str(e)}")
    
    def display_results(self, results):
        """Shows the search results - MODERN UI UPGRADE"""
        self.results_list.clear()
        
        for result in results:
            item = QListWidgetItem()
            
            # Enhanced item text and icon based on type
            if 'type' in result and result['type'] == 'calculation':
                # Math calculation with modern formatting
                item.setText(f"🧮  {result['filename']}")
                item.setToolTip("Mathematical calculation")
            elif 'type' in result and result['type'] == 'command':
                # Command with settings icon
                item.setText(f"⚙️  {result['filename']}")
                item.setToolTip("BetterFinder command")
            else:
                # Enhanced file display with better formatting
                filename = result['filename']
                path = result['path']
                
                # File type icons based on extension
                file_icon = self.get_file_icon(filename)
                
                # Format: Icon + Filename + Path (secondary color)
                display_text = f"{file_icon}  {filename}"
                if path and path != filename:
                    # Truncate long paths for better readability
                    if len(path) > 50:
                        path = "..." + path[-47:]
                    display_text += f"\n    📁 {path}"
                
                item.setText(display_text)
                item.setToolTip(result.get('full_path', ''))
            
            # Data for double click storage
            item.setData(Qt.UserRole, result['full_path'])
            
            # Enhanced styling for individual items
            font = item.font()
            font.setFamily(FONT_FAMILY)
            item.setFont(font)
            
            self.results_list.addItem(item)
    
    def get_file_icon(self, filename):
        """Returns appropriate emoji icon based on file extension"""
        if not filename:
            return "📄"
            
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # Icon mapping for common file types
        icon_map = {
            # Documents
            'pdf': '📕', 'doc': '📘', 'docx': '📘', 'txt': '📄', 'rtf': '📄',
            'odt': '📄', 'pages': '📄',
            
            # Spreadsheets
            'xls': '📊', 'xlsx': '📊', 'csv': '📊', 'ods': '📊', 'numbers': '📊',
            
            # Presentations
            'ppt': '📽️', 'pptx': '📽️', 'odp': '📽️', 'key': '📽️',
            
            # Images
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'bmp': '🖼️',
            'svg': '🖼️', 'ico': '🖼️', 'tiff': '🖼️', 'webp': '🖼️',
            
            # Videos
            'mp4': '🎬', 'avi': '🎬', 'mkv': '🎬', 'mov': '🎬', 'wmv': '🎬',
            'flv': '🎬', 'webm': '🎬', 'm4v': '🎬',
            
            # Audio
            'mp3': '🎵', 'wav': '🎵', 'flac': '🎵', 'aac': '🎵', 'ogg': '🎵',
            'wma': '🎵', 'm4a': '🎵',
            
            # Archives
            'zip': '📦', 'rar': '📦', '7z': '📦', 'tar': '📦', 'gz': '📦',
            'bz2': '📦', 'xz': '📦',
            
            # Code files
            'py': '🐍', 'js': '📜', 'html': '🌐', 'css': '🎨', 'cpp': '⚙️',
            'c': '⚙️', 'java': '☕', 'php': '🐘', 'rb': '💎', 'go': '🐹',
            'rs': '🦀', 'swift': '🦉', 'kt': '🎯', 'ts': '📜',
            
            # Executables
            'exe': '⚡', 'msi': '⚡', 'app': '⚡', 'deb': '⚡', 'rpm': '⚡',
            
            # Folders (special case)
            'folder': '📁'
        }
        
        return icon_map.get(ext, '📄')
    
    def on_item_selected(self, path):
        """Handles selection of a result"""
        if path == 'settings':
            # Open settings - FIX: Import and use proper settings dialog
            self.hide()
            try:
                from app.gui.settings_dialog import SettingsDialog
                # Get parent window (MainWindow) from the spotlight window
                parent_window = None
                for widget in QApplication.topLevelWidgets():
                    if isinstance(widget, MainWindow):
                        parent_window = widget
                        break
                
                if parent_window:
                    dialog = SettingsDialog(parent_window)
                    dialog.exec_()
                else:
                    print("Warning: Could not find main window for settings dialog")
            except Exception as e:
                print(f"Error opening settings: {e}")
                import traceback
                traceback.print_exc()
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

# SettingsDialog class removed - using separate settings_dialog.py file instead

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
        """Shows the settings - FIXED"""
        try:
            from app.gui.settings_dialog import SettingsDialog
            dialog = SettingsDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                # Settings were saved
                # Update application with new settings
                self.apply_settings()
        except Exception as e:
            print(f"Error opening settings: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(f"Could not open settings: {str(e)}")
    
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
    
    def setup_autostart(self, enable):
        """Configures autostart - ADDED FOR SETTINGS DIALOG"""
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
    dark_palette.setColor(QPalette.Base, QColor(BACKGROUND_SECONDARY))
    dark_palette.setColor(QPalette.AlternateBase, QColor(BACKGROUND_COLOR))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(TEXT_COLOR))
    dark_palette.setColor(QPalette.ToolTipText, QColor(TEXT_COLOR))
    dark_palette.setColor(QPalette.Text, QColor(TEXT_COLOR))
    dark_palette.setColor(QPalette.Button, QColor(BACKGROUND_SECONDARY))
    dark_palette.setColor(QPalette.ButtonText, QColor(TEXT_COLOR))
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(ACCENT_COLOR))
    dark_palette.setColor(QPalette.Highlight, QColor(ACCENT_COLOR))
    dark_palette.setColor(QPalette.HighlightedText, Qt.white)
    
    app.setPalette(dark_palette)
    
    # Main window create (in background)
    window = MainWindow()
    
    # Application start
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 