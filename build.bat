@echo off
REM FocusClass Build Script for Windows
REM This script builds both Teacher.exe and Student.exe

echo FocusClass Build Script
echo =====================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or later and try again
    pause
    exit /b 1
)

REM Check if pip is available
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo Error: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo Python detected. Starting build process...

REM Install PyInstaller if not already installed
echo Installing PyInstaller...
python -m pip install pyinstaller

REM Run the build script
echo Running Python build script...
python build.py

if errorlevel 1 (
    echo Build failed! Check error messages above.
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Check the 'dist' directory for the executable files.
echo.
pause