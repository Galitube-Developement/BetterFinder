=============================================
BetterFinder Installer Creation - Guide
=============================================

This readme file explains how to create a professional installer for BetterFinder using Inno Setup.

Prerequisites:
---------------
1. The finished BetterFinder.exe has been created with PyInstaller (located in the "dist" directory)
2. Inno Setup is installed (Download: https://jrsoftware.org/isdl.php)

Installation steps for Inno Setup:
------------------------------------
1. Visit https://jrsoftware.org/isdl.php
2. Download the latest version of Inno Setup
3. Run the downloaded file and follow the instructions
4. Select the "Inno Setup Preprocessor" option during installation

Creating the Installer:
------------------------
1. Ensure "BetterFinder.exe" is in the "dist" directory
2. Create image files for the installer (optional):
   - wizard-image.bmp (164x314 pixels) for the left side of the installer
   - wizard-small-image.bmp (55x58 pixels) for the upper right corner
   - Save these in the "installer_assets" directory
3. Open "setup_script.iss" with Inno Setup Compiler
4. Click on "Compile" (or press F9)
5. The installer will be created in the "installer" directory

The finished installer offers:
---------------------------
- Professional appearance
- Selection of installation directory
- Options for:
  * Create desktop icon
  * Create start menu entry
  * Enable autostart
- Context menu entry for folders
- Multilingual support (German/English)
- Automatic detection of system compatibility
- Clean uninstallation with option to delete user settings

Customizations:
-----------
You can customize the following aspects of the installer:
1. Version and publisher in the #define statements at the beginning of the .iss file
2. Default installation directory in DefaultDirName
3. Layout and design by changing the WizardImageFile and WizardSmallImageFile
4. Supported languages in the [Languages] section
5. Options enabled by default by changing the Flags in [Tasks]

If you have questions or problems, contact the BetterFinder team. 