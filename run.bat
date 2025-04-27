@echo off
echo ===================================================
echo        Starting BetterFinder...
echo ===================================================
echo.

:: Cleanup of potentially running Python processes
echo Checking running Python processes...
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo Terminating running Python processes...
    taskkill /F /IM python.exe >NUL 2>&1
    timeout /t 2 /nobreak >NUL
)

:: Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python was not found!
    echo.
    echo Please install Python 3.8 or newer and run installer.bat.
    echo.
    pause
    exit /B 1
) else (
    for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
    echo Python %PYTHON_VERSION% found.
)

:: Check if dependencies are installed
echo Checking dependencies...
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo PyQt5 not installed! Installing dependencies...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Attempting individual installation of critical components...
        python -m pip install PyQt5==5.15.9
        python -m pip install pywin32==306
        if %errorlevel% neq 0 (
            echo Error installing dependencies.
            echo Please run 'installer.bat' to install all dependencies.
            pause
            exit /B 1
        )
    )
)

:: Check if old database is locked and clean up if necessary
echo Checking old database files...
set DB_PATH=%USERPROFILE%\BetterFinder
if exist "%DB_PATH%\index.db" (
    echo Ensuring database is not locked...
    :: Try to delete the WAL file if it exists
    if exist "%DB_PATH%\index.db-wal" (
        del /F /Q "%DB_PATH%\index.db-wal" >nul 2>&1
        if exist "%DB_PATH%\index.db-wal" (
            echo Warning: Could not delete WAL file, database may be locked.
        ) else (
            echo WAL file successfully removed.
        )
    )
    if exist "%DB_PATH%\index.db-shm" (
        del /F /Q "%DB_PATH%\index.db-shm" >nul 2>&1
        if exist "%DB_PATH%\index.db-shm" (
            echo Warning: Could not delete SHM file, database may be locked.
        ) else (
            echo SHM file successfully removed.
        )
    )
    
    :: Optional: Create a backup in case of frequent database problems
    if not exist "%DB_PATH%\index.db.bak" (
        echo Creating database backup...
        copy "%DB_PATH%\index.db" "%DB_PATH%\index.db.bak" >nul 2>&1
    )
)

:: Start the program
echo.
echo ===================================================
echo Starting BetterFinder...
echo ===================================================
python -m app.main

:: Error handling
if %errorlevel% neq 0 (
    echo.
    echo BetterFinder exited with an error (Code: %errorlevel%).
    echo.
    echo Possible solutions for problems:
    echo.
    echo 1. Make sure no other instance of BetterFinder is running.
    echo 2. For database problems, try:
    echo    a) Remove the database file:
    echo       del "%USERPROFILE%\BetterFinder\index.db"
    echo    b) Restore the backup (if available):
    echo       copy "%USERPROFILE%\BetterFinder\index.db.bak" "%USERPROFILE%\BetterFinder\index.db"
    echo 3. Run 'installer.bat' again to update all components.
    echo.
    
    choice /C YN /M "Do you want to reset the database (Y/N)? "
    if %errorlevel% equ 1 (
        echo Resetting database...
        if exist "%DB_PATH%\index.db" del /F /Q "%DB_PATH%\index.db"
        if exist "%DB_PATH%\index.db-wal" del /F /Q "%DB_PATH%\index.db-wal"
        if exist "%DB_PATH%\index.db-shm" del /F /Q "%DB_PATH%\index.db-shm"
        echo Database has been reset. Restart BetterFinder.
    )
    
    pause
) 