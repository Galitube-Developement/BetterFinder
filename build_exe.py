"""
BetterFinder executable builder script

This script builds a standalone executable of BetterFinder using PyInstaller.
It handles:
1. Cleaning up previous build files
2. Creating an executable with the correct icon
3. Copying the executable to the right location
"""

import os
import sys
import shutil
import subprocess
import traceback

def print_header(text):
    """Prints a formatted header text"""
    print("=" * 30)
    print(text)
    print("=" * 30)

def is_process_running(process_name):
    """Checks if a process with the given name is running"""
    try:
        # Windows method using tasklist
        result = subprocess.run(
            f'tasklist /FI "IMAGENAME eq {process_name}" /NH', 
            shell=True, 
            capture_output=True, 
            text=True
        )
        return process_name.lower() in result.stdout.lower()
    except Exception as e:
        print(f"Error checking for running process: {e}")
        return False

def terminate_process(process_name):
    """Tries to terminate a process with the given name"""
    try:
        subprocess.run(f'taskkill /F /IM {process_name}', shell=True)
        print(f"Terminated {process_name}")
        return True
    except Exception as e:
        print(f"Error terminating process: {e}")
        return False

def clean_build_directories():
    """Removes previous build directories"""
    directories = ['build', 'dist']
    for directory in directories:
        if os.path.exists(directory):
            try:
                print(f"Removing existing {directory} directory...")
                shutil.rmtree(directory)
            except Exception as e:
                print(f"Error removing {directory}: {e}")
                traceback.print_exc()
                return False
    return True

def clean_spec_file():
    """Removes previous spec file"""
    spec_file = "BetterFinder.spec"
    if os.path.exists(spec_file):
        try:
            os.remove(spec_file)
            print(f"Removed existing {spec_file}.")
            return True
        except Exception as e:
            print(f"Error removing {spec_file}: {e}")
            return False
    return True

def clean_exe_file():
    """Removes previous executable in the root directory"""
    exe_file = "BetterFinder.exe"
    if os.path.exists(exe_file):
        try:
            os.remove(exe_file)
            print(f"Removed existing {exe_file}.")
            return True
        except Exception as e:
            print(f"Error removing {exe_file}: {e}")
            return False
    return True

def find_icon():
    """Finds the icon file for the application"""
    icon_paths = [
        os.path.join("app", "resources", "icon.ico"),
        os.path.join("app", "resources", "BetterFinder-Icon.ico"),
        "icon.ico",
        "BetterFinder-Icon.ico"
    ]
    
    for path in icon_paths:
        if os.path.exists(path):
            print(f"Using icon: {path}")
            return path
    
    # If no icon found, try to create one
    try:
        from create_icon import create_icon_from_png
        png_path = os.path.join("app", "resources", "BetterFinder-Icon.png")
        ico_path = os.path.join("app", "resources", "icon.ico")
        
        if os.path.exists(png_path):
            print("Creating icon from PNG...")
            if create_icon_from_png(png_path, ico_path):
                return ico_path
    except Exception as e:
        print(f"Error creating icon: {e}")
    
    print("Warning: No icon found. Using default PyInstaller icon.")
    return None

def build_executable(icon_path=None):
    """Builds the executable using PyInstaller"""
    try:
        # Base command
        cmd = [
            "pyinstaller",
            "--name=BetterFinder",
            "--onefile",
            "--windowed",
            "--clean",
            "--noconfirm",
            "--add-data=app/resources;app/resources"
        ]
        
        # Add icon if available
        if icon_path:
            cmd.append(f"--icon={icon_path}")
        
        # Add main script
        cmd.append("app/main.py")
        
        # Convert command to string for printing
        cmd_str = " ".join(cmd)
        print("Starting PyInstaller...")
        print(f"Command: {cmd_str}")
        
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Print output
        print(result.stdout)
        
        if result.stderr:
            print("Errors/Warnings:")
            print(result.stderr)
        
        if result.returncode != 0:
            print(f"PyInstaller failed with code {result.returncode}")
            return False
        
        return True
    except Exception as e:
        print(f"Error building executable: {e}")
        traceback.print_exc()
        return False

def copy_executable():
    """Copies the executable from the dist directory to the current directory"""
    source = os.path.join("dist", "BetterFinder.exe")
    destination = "BetterFinder.exe"
    
    if os.path.exists(source):
        try:
            shutil.copy2(source, destination)
            return True
        except Exception as e:
            print(f"Error copying executable: {e}")
            return False
    else:
        print(f"Error: {source} not found")
        return False

def main():
    """Main function to build the executable"""
    print_header("BetterFinder .exe Builder")
    
    # Check for running processes
    process_name = "BetterFinder.exe"
    if is_process_running(process_name):
        print(f"Trying to terminate running {process_name} processes...")
        terminate_process(process_name)
    
    # Clean up previous build files
    if not clean_build_directories():
        print("Error cleaning build directories. Continuing anyway...")
    
    if not clean_spec_file():
        print("Error cleaning spec file. Continuing anyway...")
    
    if not clean_exe_file():
        print("Error cleaning executable. Continuing anyway...")
    
    # Find icon
    icon_path = find_icon()
    
    # Build the executable
    if build_executable(icon_path):
        # Copy the executable to the current directory
        if copy_executable():
            print("\nBuild completed successfully!")
            print(f"The executable has been created at: {os.path.abspath(os.path.join('dist', 'BetterFinder.exe'))}")
            print("You can now use this file on any Windows computer, even without Python installation.")
            print(f"A copy has also been created in the current directory: {os.path.abspath('BetterFinder.exe')}")
            return 0
    
    print("\nBuild failed!")
    return 1

if __name__ == "__main__":
    sys.exit(main()) 