"""
Build Configuration for FocusClass

This file defines the necessary configurations for building the FocusClass application,
including dependencies, platform-specific settings, and build scripts.
"""

import sys
from pathlib import Path

# --- Project Metadata ---
APP_NAME = "FocusClass"
APP_VERSION = "1.0.0"
AUTHOR = "FocusClass Team"
EMAIL = "support@focusclass.app"
DESCRIPTION = "Professional Classroom Management System"

# --- Build Directories ---
BASE_DIR = Path(__file__).parent
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
LOG_DIR = BASE_DIR / "logs"

# --- Core Dependencies ---
# List of essential packages required for the application to run
CORE_DEPENDENCIES = [
    "PyQt5==5.15.10",
    "qasync==0.23.0",
    "numpy==1.26.4",
    "opencv-python==4.9.0.80",
    "mss==9.0.1",
    "pyqrcode==1.2.1",
    "pypng==0.20220715.0",
    "pillow==10.3.0",
    "websockets==12.0",
    "netifaces==0.11.0"
]

# --- Development and Build Dependencies ---
# Packages required for building, testing, and packaging
DEV_DEPENDENCIES = [
    "pyinstaller==6.6.0",
    "pytest==8.2.0",
    "pytest-qt==4.2.0",
    "faker==25.2.0"
]

# --- Platform-Specific Settings ---
# Adjustments for different operating systems (Windows, macOS, Linux)

PLATFORM = sys.platform
ICON_PATH = BASE_DIR / "assets" / "icon.ico"
if PLATFORM == "darwin":  # macOS
    ICON_PATH = BASE_DIR / "assets" / "icon.icns"
elif PLATFORM == "linux":
    ICON_PATH = BASE_DIR / "assets" / "icon.png"

# --- PyInstaller Configuration ---
# Settings for creating the executable file

PYINSTALLER_CONFIG = {
    "name": APP_NAME,
    "version": APP_VERSION,
    "script": str(BASE_DIR / "FocusClass.py"),
    "icon": str(ICON_PATH),
    "distpath": str(DIST_DIR),
    "buildpath": str(BUILD_DIR),
    "specpath": str(BASE_DIR),
    "onefile": True,
    "windowed": True,
    "noconfirm": True,
    "clean": True,
    "additional_hooks": [],
    "hidden_imports": [
        "PyQt5.sip",
        "numpy",
        "websockets.legacy.server",
        "websockets.legacy.client",
        "asyncio"
    ],
    "datas": [
        (str(BASE_DIR / "src"), "src"),
        (str(BASE_DIR / "assets"), "assets")
    ],
    "excludes": ["tkinter"],
    "upx_dir": None  # Set path to UPX if you want to use it
}

# --- Production Readiness Checklist ---
PRODUCTION_CHECKLIST = {
    "tests_passed": False,
    "dependencies_frozen": False,
    "version_updated": False,
    "changelog_generated": False,
    "executable_built": False,
    "installer_created": False
}

# --- Functions ---

def get_all_dependencies():
    """Returns a combined list of core and development dependencies."""
    return CORE_DEPENDENCIES + DEV_DEPENDENCIES

def generate_requirements_file(path=BASE_DIR / "requirements.txt"):
    """Generates a requirements.txt file from the dependency lists."""
    print(f"Generating requirements file at: {path}")
    with open(path, "w") as f:
        f.write("# --- Core Dependencies ---\n")
        f.write("\n".join(CORE_DEPENDENCIES))
        f.write("\n\n# --- Development Dependencies ---\n")
        f.write("\n".join(DEV_DEPENDENCIES))
    print("Requirements file generated successfully.")

if __name__ == "__main__":
    # This allows the script to be run directly to generate requirements.txt
    print("Running build configuration setup...")
    generate_requirements_file()
    print("\nBuild Configuration:")
    print(f"  - App Name: {APP_NAME}")
    print(f"  - App Version: {APP_VERSION}")
    print(f"  - Platform: {PLATFORM}")
    print(f"  - Dist Directory: {DIST_DIR}")
    print(f"  - Icon Path: {ICON_PATH}")
    print("\nTo build the project, run 'build_production.py'.")
block_cipher = None

a = Analysis(
    ['src/student/student_app.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('src/common', 'src/common'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'PyQt5.sip',
        'asyncio',
        'websockets',
        'aiortc',
        'aiortc.contrib.media',
        'mss',
        'cv2',
        'PIL',
        'numpy',
        'qrcode',
        'zeroconf',
        'win32api',
        'win32con',
        'win32gui',
        'win32process',
        'win32security',
        'psutil',
        'qasync',
        'av',
        'fractions',
        'ctypes',
        'json',
        'threading',
        'multiprocessing',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Student',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/student_icon.ico' if os.path.exists('assets/student_icon.ico') else None,
)
"""


def generate_spec_files():
    """Generate PyInstaller spec files"""
    with open('teacher.spec', 'w') as f:
        f.write(teacher_spec)
    
    with open('student.spec', 'w') as f:
        f.write(student_spec)
    
    print("Generated spec files: teacher.spec, student.spec")


if __name__ == "__main__":
    generate_spec_files()