"""
Main entry point for BetterFinder

This module starts the application and initializes all required components.
"""

import sys
import os
import argparse
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from app.gui.main_window import MainWindow


def parse_arguments():
    """
    Parses command line arguments
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="BetterFinder - Fast file search for Windows")
    
    # Arguments for command line usage
    parser.add_argument("--search", help="Performs a search and outputs the results")
    parser.add_argument("--type", help="Filters the search by file type (e.g. .txt, .pdf)")
    parser.add_argument("--reindex", action="store_true", help="Reindexes the file system")
    
    return parser.parse_args()


def run_command_line(args):
    """
    Executes command line commands
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        True if the application should start in GUI mode,
        False if it should exit
    """
    # If --reindex was specified
    if args.reindex:
        print("Performing indexing...")
        # A direct indexing would happen here
        # In this case we still start the GUI, which handles the indexing
        return True
        
    # If a search should be performed
    if args.search:
        print(f"Searching for: {args.search}")
        if args.type:
            print(f"File type filter: {args.type}")
        # A direct search could be implemented here
        # For this version we start the GUI
        return True
        
    # Start GUI by default
    return True


def set_app_icon(app):
    """Sets the application icon for the BetterFinder application"""
    icon_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "icon.ico"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "BetterFinder-Icon.png")
    ]
    
    # If we are in a frozen PyInstaller application, the path is different
    if getattr(sys, 'frozen', False):
        # For PyInstaller build
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        icon_paths.extend([
            os.path.join(base_path, "app", "resources", "icon.ico"),
            os.path.join(base_path, "app", "resources", "BetterFinder-Icon.png"),
            os.path.join(base_path, "resources", "icon.ico"),
            os.path.join(base_path, "resources", "BetterFinder-Icon.png")
        ])
    
    # Try to load the icon from various possible paths
    for icon_path in icon_paths:
        if os.path.exists(icon_path):
            try:
                app.setWindowIcon(QIcon(icon_path))
                print(f"Icon set from: {icon_path}")
                return True
            except Exception as e:
                print(f"Error setting icon from {icon_path}: {e}")
    
    print("Warning: No valid icon found")
    return False


def main():
    """
    Main entry point
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Check if a command line command should be executed
    should_start_gui = run_command_line(args)
    
    if should_start_gui:
        # Start GUI mode
        app = QApplication(sys.argv)
        app.setApplicationName("BetterFinder")
        app.setOrganizationName("BetterFinder")
        
        # Set the application icon
        set_app_icon(app)
        
        # Create main window (with tray icon, no visible window)
        window = MainWindow()
        
        # Run application
        sys.exit(app.exec_())


if __name__ == "__main__":
    main() 