"""Production-Ready Build Script for FocusClass
Enhanced PyInstaller configuration with comprehensive bundling
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are available"""
    logger.info("Checking build dependencies...")
    
    required_modules = [
        'PyInstaller',
        'PyQt5',
        'qasync',
        'websockets',
        'mss',
        'psutil',
        'PIL',
        'qrcode',
        'numpy'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            logger.info(f"✓ {module} - Available")
        except ImportError:
            missing_modules.append(module)
            logger.warning(f"✗ {module} - Missing")
    
    if missing_modules:
        logger.error(f"Missing required modules: {', '.join(missing_modules)}")
        logger.error("Please install missing modules using: pip install -r requirements.txt")
        return False
    
    logger.info("All required dependencies are available")
    return True

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            logger.info(f"Cleaning {dir_name} directory...")
            shutil.rmtree(dir_name)
    
    # Clean .spec files
    for spec_file in Path('.').glob('*.spec'):
        logger.info(f"Removing {spec_file}...")
        spec_file.unlink()

def ensure_directories():
    """Ensure required directories exist"""
    required_dirs = ['logs', 'exports', 'assets']
    
    for dir_name in required_dirs:
        Path(dir_name).mkdir(exist_ok=True)
        logger.info(f"Ensured {dir_name} directory exists")

def create_production_spec():
    """Create comprehensive PyInstaller spec file"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Get the base directory
base_dir = Path(SPECPATH)

# Define data files and directories to include
datas = [
    (str(base_dir / 'src'), 'src'),
    (str(base_dir / 'assets'), 'assets'),
    (str(base_dir / 'README.md'), '.'),
    (str(base_dir / 'requirements.txt'), '.'),
]

# Hidden imports for proper module resolution
hiddenimports = [
    'qasync',
    'asyncio',
    'PyQt5.QtCore',
    'PyQt5.QtGui', 
    'PyQt5.QtWidgets',
    'PyQt5.QtNetwork',
    'websockets',
    'websockets.server',
    'websockets.client',
    'mss',
    'psutil',
    'sqlite3',
    'json',
    'csv',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'numpy',
    'cv2',
    'qrcode',
    'qrcode.image.pil',
    'pkg_resources',
]

# Try to include optional dependencies
try:
    import aiortc
    hiddenimports.extend([
        'aiortc',
        'aiortc.contrib.media',
        'av',
        'av.video',
        'av.audio',
    ])
except ImportError:
    pass

try:
    import win32gui
    hiddenimports.extend([
        'win32gui',
        'win32con',
        'win32api',
        'win32process',
    ])
except ImportError:
    pass

# Analysis configuration
a = Analysis(
    ['FocusClass.py'],
    pathex=[str(base_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate binaries
a.binaries = [x for x in a.binaries if not x[0].startswith('api-ms-win')]

# PYZ archive
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FocusClass',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windows app, not console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,  # Request admin privileges
    icon=str(base_dir / 'assets' / 'icon.ico') if (base_dir / 'assets' / 'icon.ico').exists() else None,
)

# Collection for distribution
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FocusClass',
)
'''
    
    with open('FocusClass_Production.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    logger.info("Created production PyInstaller spec file")

def build_application():
    """Build the application using PyInstaller"""
    logger.info("Starting PyInstaller build process...")
    
    # Run PyInstaller with the spec file
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        'FocusClass_Production.spec'
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("PyInstaller build completed successfully")
        
        if result.stdout:
            logger.info(f"PyInstaller output: {result.stdout}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"PyInstaller build failed: {e}")
        if e.stdout:
            logger.error(f"STDOUT: {e.stdout}")
        if e.stderr:
            logger.error(f"STDERR: {e.stderr}")
        raise

def create_installer_script():
    """Create an NSIS installer script for Windows"""
    nsis_script = f'''
; FocusClass Professional Installer
!define APP_NAME "FocusClass Professional"
!define APP_VERSION "1.0.0"
!define PUBLISHER "FocusClass Team"
!define WEB_SITE "https://github.com/focusclass/focusclass"
!define APP_EXE "FocusClass.exe"

!include "MUI2.nsh"

; Request admin privileges
RequestExecutionLevel admin

; Interface settings
!define MUI_ABORTWARNING
!define MUI_ICON "assets\\\\icon.ico"
!define MUI_UNICON "assets\\\\icon.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "README.md"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installer details
Name "${{APP_NAME}}"
OutFile "FocusClass_Professional_Setup.exe"
InstallDir "$PROGRAMFILES\\\\FocusClass"
InstallDirRegKey HKLM "Software\\\\${{APP_NAME}}" "Install_Dir"

; Version information
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "${{APP_NAME}}"
VIAddVersionKey "CompanyName" "${{PUBLISHER}}"
VIAddVersionKey "FileVersion" "${{APP_VERSION}}"
VIAddVersionKey "ProductVersion" "${{APP_VERSION}}"
VIAddVersionKey "FileDescription" "Professional Classroom Management System"

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    SetOverwrite ifnewer
    
    ; Copy all files
    File /r "dist\\\\FocusClass\\\\*"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\\\\FocusClass"
    CreateShortCut "$SMPROGRAMS\\\\FocusClass\\\\FocusClass Professional.lnk" "$INSTDIR\\\\${{APP_EXE}}"
    CreateShortCut "$DESKTOP\\\\FocusClass Professional.lnk" "$INSTDIR\\\\${{APP_EXE}}"
    
    ; Registry entries
    WriteRegStr HKLM "Software\\\\${{APP_NAME}}" "Install_Dir" "$INSTDIR"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APP_NAME}}" "DisplayName" "${{APP_NAME}}"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APP_NAME}}" "UninstallString" '"$INSTDIR\\\\uninstall.exe"'
    WriteRegDWORD HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APP_NAME}}" "NoModify" 1
    WriteRegDWORD HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APP_NAME}}" "NoRepair" 1
    WriteUninstaller "uninstall.exe"
SectionEnd

Section "Uninstall"
    ; Remove registry keys
    DeleteRegKey HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APP_NAME}}"
    DeleteRegKey HKLM "Software\\\\${{APP_NAME}}"
    
    ; Remove files and directories
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$SMPROGRAMS\\\\FocusClass\\\\*"
    RMDir "$SMPROGRAMS\\\\FocusClass"
    Delete "$DESKTOP\\\\FocusClass Professional.lnk"
SectionEnd
'''
    
    with open('installer.nsi', 'w', encoding='utf-8') as f:
        f.write(nsis_script)
    
    logger.info("Created NSIS installer script")

def create_batch_installer():
    """Create a simple batch installer as backup"""
    batch_script = '''@echo off
echo ============================================
echo    FocusClass Professional Installer
echo ============================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Administrator privileges confirmed.
) else (
    echo ERROR: This installer requires administrator privileges.
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo.
set /p INSTALL_DIR="Enter installation directory (default: C:\\Program Files\\FocusClass): "
if "%INSTALL_DIR%"=="" set INSTALL_DIR=C:\\Program Files\\FocusClass

echo.
echo Installing FocusClass to: %INSTALL_DIR%
echo.

REM Create installation directory
mkdir "%INSTALL_DIR%" 2>nul

REM Copy files
echo Copying application files...
xcopy /E /I /Y "dist\\FocusClass\\*" "%INSTALL_DIR%\\"

if %errorLevel% == 0 (
    echo ✓ Files copied successfully
) else (
    echo ✗ Error copying files
    pause
    exit /b 1
)

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\FocusClass Professional.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\FocusClass.exe'; $Shortcut.Save()"

REM Create start menu shortcut
echo Creating start menu shortcut...
mkdir "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\FocusClass" 2>nul
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\FocusClass\\FocusClass Professional.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\FocusClass.exe'; $Shortcut.Save()"

echo.
echo ============================================
echo    Installation Completed Successfully!
echo ============================================
echo.
echo FocusClass has been installed to:
echo %INSTALL_DIR%
echo.
echo Shortcuts created:
echo - Desktop: FocusClass Professional
echo - Start Menu: FocusClass Professional
echo.
echo You can now run FocusClass from the desktop shortcut
echo or start menu.
echo.
pause
'''
    
    with open('install.bat', 'w', encoding='utf-8') as f:
        f.write(batch_script)
    
    logger.info("Created batch installer script")

def post_build_cleanup():
    """Post-build cleanup and organization"""
    logger.info("Performing post-build cleanup...")
    
    dist_dir = Path('dist/FocusClass')
    if dist_dir.exists():
        # Create logs and exports directories in the distribution
        (dist_dir / 'logs').mkdir(exist_ok=True)
        (dist_dir / 'exports').mkdir(exist_ok=True)
        
        # Copy additional files
        additional_files = ['README.md', 'requirements.txt']
        for file_name in additional_files:
            src_file = Path(file_name)
            if src_file.exists():
                shutil.copy2(src_file, dist_dir / file_name)
                logger.info(f"Copied {file_name} to distribution")
        
        # Calculate distribution size
        total_size = sum(f.stat().st_size for f in dist_dir.rglob('*') if f.is_file())
        
        logger.info(f"Build completed successfully!")
        logger.info(f"Executable location: {dist_dir / 'FocusClass.exe'}")
        logger.info(f"Distribution size: ~{total_size / 1024 / 1024:.1f} MB")
    else:
        logger.error("Distribution directory not found!")

def main():
    """Main build process"""
    start_time = datetime.now()
    logger.info(f"Starting FocusClass production build at {start_time}")
    
    try:
        # Step 0: Check dependencies
        if not check_dependencies():
            logger.error("Missing dependencies. Please install required modules.")
            sys.exit(1)
        
        # Step 1: Clean previous builds
        clean_build_dirs()
        
        # Step 2: Ensure required directories
        ensure_directories()
        
        # Step 3: Create production spec file
        create_production_spec()
        
        # Step 4: Build application
        build_application()
        
        # Step 5: Create installer scripts
        create_installer_script()
        create_batch_installer()
        
        # Step 6: Post-build cleanup
        post_build_cleanup()
        
        end_time = datetime.now()
        build_duration = end_time - start_time
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎉 BUILD COMPLETED SUCCESSFULLY!")
        logger.info(f"{'='*60}")
        logger.info(f"Build Duration: {build_duration}")
        logger.info(f"Output Directory: dist/FocusClass/")
        logger.info(f"Main Executable: dist/FocusClass/FocusClass.exe")
        logger.info(f"")
        logger.info(f"📦 Installation Options:")
        logger.info(f"  • Batch Installer: install.bat (Simple)")
        logger.info(f"  • NSIS Installer: installer.nsi (Advanced)")
        logger.info(f"")
        logger.info(f"🚀 To create Windows installer:")
        logger.info(f"   makensis installer.nsi")
        logger.info(f"")
        logger.info(f"🔧 To install directly:")
        logger.info(f"   Run install.bat as Administrator")
        logger.info(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()