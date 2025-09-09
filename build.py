#!/usr/bin/env python3
"""
Build script for FocusClass Application
Generates standalone executable with administrator privileges
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False


def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    required_packages = ["PyQt5", "qasync", "PyInstaller", "Pillow", "qrcode", "aiosqlite", "websockets", "psutil"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print(f"Install with: pip install {' '.join(missing_packages)}")
        return False
    return True


def create_spec_file():
    """Create PyInstaller spec file"""
    print("\nCreating PyInstaller spec file...")
    
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

project_root = Path(SPECPATH)
sys.path.insert(0, str(project_root))

block_cipher = None

a = Analysis(
    ['FocusClass.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[('src', 'src'), ('assets', 'assets')],
    hiddenimports=[
        'PyQt5.sip', 'asyncio', 'websockets', 'aiosqlite', 'mss', 'PIL',
        'qrcode', 'psutil', 'qasync', 'ctypes', 'json', 'sqlite3',
        'threading', 'multiprocessing', 'win32api', 'win32con',
        'win32gui', 'win32process', 'win32security',
    ],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[],
    win_no_prefer_redirects=False, win_private_assemblies=False,
    cipher=block_cipher, noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='FocusClass', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, upx_exclude=[], runtime_tmpdir=None,
    console=False, disable_windowed_traceback=False, argv_emulation=False,
    target_arch=None, codesign_identity=None, entitlements_file=None,
    uac_admin=True, icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)
"""
    
    with open('FocusClass.spec', 'w') as f:
        f.write(spec_content)
    
    print("✓ Created FocusClass.spec")
    return True


def create_assets():
    """Create assets directory"""
    assets_dir = Path('assets')
    assets_dir.mkdir(exist_ok=True)
    
    # Create logs directory
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    print("✓ Created assets and logs directories")
    return True


def build_executable():
    """Build the main executable"""
    print("\nBuilding FocusClass executable...")
    
    # Clean previous builds
    for path in ['build', 'dist']:
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"✓ Cleaned {path} directory")
    
    # Build with PyInstaller
    command = [sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', 'FocusClass.spec']
    success = run_command(command, "Building executable")
    
    if success:
        exe_path = Path('dist/FocusClass.exe')
        if exe_path.exists():
            print(f"\n✓ Executable created: {exe_path.absolute()}")
            print(f"✓ File size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
            return True
        else:
            print("✗ Executable not found after build")
    return False


def create_installer():
    """Create installation package"""
    print("\nCreating installer...")
    
    # Copy additional files to dist
    files_to_copy = [
        ('README.md', 'dist/README.md'),
        ('requirements.txt', 'dist/requirements.txt')
    ]
    
    for src, dst in files_to_copy:
        if Path(src).exists():
            try:
                shutil.copy2(src, dst)
                print(f"✓ Copied {src}")
            except Exception as e:
                print(f"✗ Failed to copy {src}: {e}")
    
    # Create installer script
    installer_script = """@echo off
echo FocusClass Professional Installer
echo.
echo Installing FocusClass...

net session >nul 2>&1
if %errorLevel% == 0 (
    echo Creating installation directory...
    if not exist "C:\\Program Files\\FocusClass" mkdir "C:\\Program Files\\FocusClass"
    
    echo Copying files...
    copy "FocusClass.exe" "C:\\Program Files\\FocusClass\\"
    
    echo Creating desktop shortcut...
    powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut(\"$env:USERPROFILE\\Desktop\\FocusClass.lnk\"); $Shortcut.TargetPath = \"C:\\Program Files\\FocusClass\\FocusClass.exe\"; $Shortcut.Save()"
    
    echo.
    echo Installation completed successfully!
    echo You can now run FocusClass from your desktop.
    echo.
    pause
) else (
    echo ERROR: Administrator privileges required!
    echo Please right-click this file and select "Run as administrator".
    echo.
    pause
)"""
    
    with open('dist/install.bat', 'w') as f:
        f.write(installer_script)
    
    print("✓ Installer script created")
    return True


def main():
    """Main build process"""
    print("🚀 FocusClass Build Process Started")
    print("=" * 50)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n❌ Build failed: Missing dependencies")
        return False
    
    # Step 2: Create assets
    if not create_assets():
        print("\n❌ Build failed: Asset creation failed")
        return False
    
    # Step 3: Create spec file
    if not create_spec_file():
        print("\n❌ Build failed: Spec file creation failed")
        return False
    
    # Step 4: Build executable
    if not build_executable():
        print("\n❌ Build failed: Executable creation failed")
        return False
    
    # Step 5: Create installer
    if not create_installer():
        print("\n❌ Build failed: Installer creation failed")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 BUILD COMPLETED SUCCESSFULLY!")
    print("\n📁 Output files:")
    print("   • Executable: dist/FocusClass.exe")
    print("   • Installer: dist/install.bat")
    print("\n🔧 To install: Run 'dist/install.bat' as Administrator")
    print("⚠️  Important: Run FocusClass as Administrator for full functionality")
    return True


if __name__ == "__main__":
    try:
        success = main()
        input("\nPress Enter to exit...")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Build failed with unexpected error: {e}")
        sys.exit(1)