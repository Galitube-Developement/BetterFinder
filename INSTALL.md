# Installing BetterFinder

## Prerequisites

- Windows 10 or newer
- Python 3.8 or newer
- pip (Python package manager)

## Installation

1. **Install Python dependencies:**

   ```
   pip install -r requirements.txt
   ```

2. **Start the program:**

   ```
   python -m app.main
   ```

## Alternative: Create an executable file

You can create a standalone .exe file:

1. **Install PyInstaller:**

   ```
   pip install pyinstaller
   ```

2. **Create the executable file:**

   ```
   pyinstaller --onefile --windowed --icon=BetterFinder-Icon.png --add-data "BetterFinder-Icon.png;." --name BetterFinder app/main.py
   ```

3. **Find the created .exe file:**

   After completion, you will find BetterFinder.exe in the "dist" directory.

## Usage

1. **Start BetterFinder**
2. **Wait until indexing is complete**
3. **Enter the search term and see immediate results**

## Features

- Fast file system indexing
- Immediate search results
- Support for advanced search operators (AND, OR, NOT)
- Wildcard search with * and ?
- Regular expressions with prefix "regex:"
- File type filtering 