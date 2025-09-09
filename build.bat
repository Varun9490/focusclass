@echo off
REM ============================================================================
REM  FocusClass Build Script
REM
REM  This script automates the process of building the FocusClass application
REM  for production. It ensures all necessary steps are taken to create a
REM  clean, reliable executable.
REM
REM  Usage:
REM    build.bat
REM
REM ============================================================================

echo [INFO] Setting up build environment...
set "PYTHON_EXE=python"
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [INFO] Verifying Python installation...
%PYTHON_EXE% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in PATH.
    echo [ERROR] Please install Python 3.8+ and add it to your system's PATH.
    goto :eof
)

echo [INFO] Starting FocusClass production build...

REM Run the main build script
%PYTHON_EXE% build_production.py

if %errorlevel% neq 0 (
    echo [ERROR] Build failed. Please check the logs above for details.
    goto :eof
)

echo [SUCCESS] Build process completed successfully.
echo [INFO] The executable can be found in the 'dist' directory.

pause