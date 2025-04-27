"""
Settings dialog for BetterFinder

This module defines the settings dialog with options for:
1. Hotkey configuration
2. Autostart settings
3. Excluded directories
4. Maximum search results
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QListWidget, QGroupBox, QSpinBox, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QSettings

class SettingsDialog(QDialog):
    """Settings dialog for BetterFinder"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.settings = QSettings("BetterFinder", "BetterFinder")
        self.setWindowTitle("BetterFinder Settings")
        self.resize(500, 400)
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Hotkey group
        hotkey_group = QGroupBox("Hotkey")
        hotkey_layout = QVBoxLayout(hotkey_group)
        hotkey_description = QLabel("Hotkey to open BetterFinder:")
        self.hotkey_edit = QLineEdit()
        self.hotkey_button = QPushButton("Change")
        self.hotkey_button.clicked.connect(self.change_hotkey)
        hotkey_layout.addWidget(hotkey_description)
        hotkey_layout.addWidget(self.hotkey_edit)
        hotkey_layout.addWidget(self.hotkey_button)
        
        # Autostart group
        autostart_group = QGroupBox("System Start")
        autostart_layout = QVBoxLayout(autostart_group)
        self.autostart_checkbox = QCheckBox("Start BetterFinder automatically at system start")
        autostart_layout.addWidget(self.autostart_checkbox)
        
        # Excluded paths group
        exclude_group = QGroupBox("Excluded Directories")
        exclude_layout = QVBoxLayout(exclude_group)
        exclude_description = QLabel("These directories will not be indexed:")
        self.exclude_list = QListWidget()
        exclude_buttons_layout = QHBoxLayout()
        self.add_exclude_button = QPushButton("Add")
        self.add_exclude_button.clicked.connect(self.add_exclude_path)
        self.remove_exclude_button = QPushButton("Remove")
        self.remove_exclude_button.clicked.connect(self.remove_exclude_path)
        exclude_buttons_layout.addWidget(self.add_exclude_button)
        exclude_buttons_layout.addWidget(self.remove_exclude_button)
        exclude_layout.addWidget(exclude_description)
        exclude_layout.addWidget(self.exclude_list)
        exclude_layout.addLayout(exclude_buttons_layout)
        
        # Max results group
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        results_description = QLabel("Maximum number of displayed search results:")
        self.max_results_spinbox = QSpinBox()
        self.max_results_spinbox.setRange(10, 1000)
        self.max_results_spinbox.setSingleStep(10)
        results_layout.addWidget(results_description)
        results_layout.addWidget(self.max_results_spinbox)
        
        # Add groups to main layout
        layout.addWidget(hotkey_group)
        layout.addWidget(autostart_group)
        layout.addWidget(exclude_group)
        layout.addWidget(results_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)
    
    def load_settings(self):
        """Load existing settings"""
        # Hotkey
        hotkey = self.settings.value("hotkey", "Ctrl+Space")
        self.hotkey_edit.setText(hotkey)
        
        # Autostart
        autostart = self.settings.value("autostart", False, type=bool)
        self.autostart_checkbox.setChecked(autostart)
        
        # Excluded directories
        excluded_paths = self.settings.value("excluded_paths", [], type=list)
        for path in excluded_paths:
            self.exclude_list.addItem(path)
        
        # Maximum results
        max_results = self.settings.value("max_results", 30, type=int)
        self.max_results_spinbox.setValue(max_results)
    
    def save_settings(self):
        """Saves the settings and closes the dialog."""
        try:
            # Save hotkey
            self.settings.setValue("hotkey", self.hotkey_edit.text())
            
            # Save autostart setting
            autostart = self.autostart_checkbox.isChecked()
            self.settings.setValue("autostart", autostart)
            
            # Configure autostart
            try:
                self.main_window.setup_autostart(autostart)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Autostart Error",
                    f"Settings were saved, but autostart could not be configured:\n\n{str(e)}\n\n"
                    "Possible solutions:\n"
                    "- Run the program as administrator\n"
                    "- Check permissions for the autostart folder\n"
                    "- Disable the autostart option"
                )
                # Reset autostart setting
                self.settings.setValue("autostart", False)
                self.autostart_checkbox.setChecked(False)
            
            # Save excluded paths
            paths = []
            for i in range(self.exclude_list.count()):
                paths.append(self.exclude_list.item(i).text())
            self.settings.setValue("excluded_paths", paths)
            
            # Save maximum results
            self.settings.setValue("max_results", self.max_results_spinbox.value())
            
            # Write settings to file
            self.settings.sync()
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving",
                f"The settings could not be saved:\n\n{str(e)}"
            )
            import traceback
            traceback.print_exc()
    
    def change_hotkey(self):
        """Changes the hotkey"""
        # In a real implementation, this would capture a key press
        self.hotkey_edit.setText("Ctrl+Space")
    
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